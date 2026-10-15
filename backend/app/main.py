from __future__ import annotations

import asyncio
import csv
import io

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

import sys
from pathlib import Path

from . import config, db, keywords
from .models import AnalyzeRequest, DiscoverRequest, KeywordGroup, KeywordRequest, Product
from .scoring import score_products
from .scrapers import REGISTRY, for_url

app = FastAPI(title="sh-app backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=True)


@app.get("/health")
def health():
    return {"ok": True, "app": "shapp"}


@app.get("/api/sources")
def sources():
    return [{"name": s.name, "label": s.label} for s in REGISTRY.values()]


@app.post("/api/discover", response_model=list[Product])
async def discover(req: DiscoverRequest):
    scraper = REGISTRY.get(req.source)
    if not scraper:
        raise HTTPException(404, "منبع ناشناخته")
    try:
        async with _client() as c:
            items = await scraper.discover(c, req)
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    if req.min_price:
        items = [p for p in items if p.price and p.price >= req.min_price]
    if req.max_price:
        items = [p for p in items if p.price and p.price <= req.max_price]
    items = score_products(items)
    db.upsert(items)
    return items


@app.get("/api/keywords")
def get_keywords():
    return keywords.groups()


@app.put("/api/keywords")
def put_keywords(groups: list[KeywordGroup]):
    keywords.save_groups([g.model_dump() for g in groups])
    return keywords.groups()


@app.post("/api/keywords/reset")
def reset_keywords():
    keywords.reset_groups()
    return keywords.groups()


@app.get("/api/keywords/resolve")
def resolve_keyword(q: str):
    group, terms = keywords.resolve(q)
    return {"group": group, "terms": terms}


@app.post("/api/discover_keyword")
async def discover_keyword(req: KeywordRequest):
    """کلیدواژه → همه‌ی عبارت‌های مرتبط در همه‌ی منابع انتخاب‌شده؛ ادغام، حذف تکراری، امتیازدهی."""
    group, terms = keywords.resolve(req.keyword)
    terms = [t for t in (req.terms or terms) if t.strip()]
    if not terms:
        raise HTTPException(400, "کلیدواژه خالی است")
    scrapers = [REGISTRY[s] for s in req.sources if s in REGISTRY]
    if not scrapers:
        raise HTTPException(400, "هیچ منبعی انتخاب نشده")
    found: dict[tuple[str, str], Product] = {}
    errors: list[str] = []

    async def run_source(scraper, client):
        # هر منبع پشت‌سرهم (مودبانه)، منابع مختلف هم‌زمان
        for term in terms:
            try:
                items = await scraper.discover(client, DiscoverRequest(
                    source=scraper.name, category=term, sort=req.sort, pages=req.pages))
            except Exception as e:  # یک عبارت خراب نباید کل جستجو را بخواباند
                errors.append(f"{scraper.label} «{term}»: {e}")
                continue
            for p in items:
                p.extra["term"] = term
                found.setdefault((p.source, p.source_id), p)

    async with _client() as c:
        await asyncio.gather(*(run_source(s, c) for s in scrapers))
    items = list(found.values())
    if req.min_price:
        items = [p for p in items if p.price and p.price >= req.min_price]
    if req.max_price:
        items = [p for p in items if p.price and p.price <= req.max_price]
    items = score_products(items)
    db.upsert(items)
    return {"group": group, "terms": terms, "products": items, "errors": errors}


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    scraper = for_url(req.url)
    if not scraper:
        raise HTTPException(400, "این سایت پشتیبانی نمی‌شود")
    try:
        async with _client() as c:
            main = await scraper.product(c, req.url)
            matches: list[Product] = []
            if req.cross_search and main.title:
                others = [s for s in REGISTRY.values() if s.name != scraper.name]
                res = await asyncio.gather(
                    *(s.search(c, main.title, 5) for s in others), return_exceptions=True)
                for r in res:
                    if not isinstance(r, Exception):
                        matches += r
    except (RuntimeError, ValueError) as e:
        raise HTTPException(502, str(e))
    scored = score_products([main] + matches)
    db.upsert(scored)
    return {
        "product": main,
        "other_sites": [p for p in scored if p is not main],
        "history": db.history(main.source, main.source_id),
    }


@app.post("/api/save/{source}/{source_id}")
def save(source: str, source_id: str, saved: bool = True):
    db.set_saved(source, source_id, saved)
    return {"ok": True}


@app.get("/api/saved", response_model=list[Product])
def saved():
    return db.saved_products()


@app.post("/api/export.csv")
def export(products: list[Product]):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["منبع", "عنوان", "قیمت(تومان)", "تعداد نظرات", "فروش", "امتیاز", "تعداد فروشنده",
                "امتیاز فرصت", "لینک"])
    for p in products:
        w.writerow([p.source, p.title, p.price, p.rating_count, p.sold_count, p.rating,
                    p.seller_count, p.opportunity_score, p.url])
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=products.csv"})


PORT = 8765


_last_ping = {"t": 0.0}


@app.get("/api/ping")
def ping():
    import time
    _last_ping["t"] = time.time()
    return {"ok": True}


@app.get("/api/stats")
def stats():
    top = sorted(db.all_products(500), key=lambda p: p.opportunity_score, reverse=True)[:10]
    return {**db.stats(), "top": top}


@app.get("/api/products", response_model=list[Product])
def products(limit: int = 200):
    return db.all_products(limit)


@app.get("/api/config")
def get_config():
    cfg = config.load()
    return {"lan": bool(cfg.get("lan")), "lan_url": f"http://{config.lan_ip()}:{PORT}",
            "log": str(config.CFG.parent / "log.txt")}


@app.post("/api/config")
def set_config(lan: bool):
    config.save({**config.load(), "lan": lan})
    return {"ok": True, "restart_required": True}


WEB = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent)) / (
    "web" if hasattr(sys, "_MEIPASS") else "app/web")


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/static", StaticFiles(directory=WEB), name="static")
