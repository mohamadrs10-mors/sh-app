from __future__ import annotations

import re

import httpx

from ..models import DiscoverRequest, Product, Seller
from ..util import pick, to_float, to_int
from .base import Scraper

BASE = "https://api.digikala.com"
SORTS = {"bestseller": 7, "visits": 4, "newest": 1, "cheapest": 20}


def _toman(v) -> int | None:
    """دیجی‌کالا قیمت را به ریال می‌دهد."""
    n = to_int(v)
    return n // 10 if n is not None else None


def parse_listing_item(p: dict) -> Product:
    pid = str(p["id"])
    v = p.get("default_variant") or {}
    price = _toman(pick(v, "price.selling_price"))
    old = _toman(pick(v, "price.rrp_price"))
    uri = pick(p, "url.uri", default=f"/product/dkp-{pid}/")
    return Product(
        source="digikala",
        source_id=pid,
        title=p.get("title_fa") or p.get("title_en") or "",
        url="https://www.digikala.com" + uri,
        image=pick(p, "images.main.url.0"),
        price=price,
        old_price=old if old and price and old > price else None,
        discount_percent=to_int(pick(v, "price.discount_percent")),
        rating=to_float(pick(p, "rating.rate")),
        rating_count=to_int(pick(p, "rating.count")),
        seller_count=None,
        brand=pick(p, "data_layer.brand"),
        category=pick(p, "data_layer.category"),
        in_stock=p.get("status") == "marketable",
        extra={
            "seller": pick(v, "seller.title"),
            "badges": [b.get("title") for b in (p.get("product_badges") or []) if isinstance(b, dict)],
            "fast_shipping": bool(pick(v, "properties.is_fast_shipping")),
        },
    )


def parse_product_detail(data: dict, url: str) -> Product:
    p = data.get("data", {}).get("product", data)
    variants = p.get("variants") or []
    sellers = []
    prices = []
    for v in variants:
        pr = _toman(pick(v, "price.selling_price"))
        if pr:
            prices.append(pr)
        sellers.append(Seller(name=pick(v, "seller.title", default="?"), price=pr,
                              url=pick(v, "seller.url")))
    specs: dict[str, str] = {}
    for grp in pick(p, "specifications.0.attributes", default=[]) or []:
        t, vals = grp.get("title"), grp.get("values")
        if t and vals:
            specs[t] = "، ".join(map(str, vals))
    best = pick(p, "default_variant") or (variants[0] if variants else {})
    price = _toman(pick(best, "price.selling_price")) or (min(prices) if prices else None)
    old = _toman(pick(best, "price.rrp_price"))
    pid = str(p.get("id"))
    return Product(
        source="digikala",
        source_id=pid,
        title=p.get("title_fa") or "",
        url=url,
        image=pick(p, "images.main.url.0"),
        price=price,
        old_price=old if old and price and old > price else None,
        discount_percent=to_int(pick(best, "price.discount_percent")),
        rating=to_float(pick(p, "rating.rate")),
        rating_count=to_int(pick(p, "rating.count")),
        seller_count=len(sellers) or None,
        brand=pick(p, "brand.title_fa", "data_layer.brand"),
        category=pick(p, "category.title_fa", "data_layer.category"),
        in_stock=p.get("status") == "marketable",
        sellers=sellers,
        specs=specs,
        extra={
            "comments_count": to_int(pick(p, "comments_count", "review.comments_count")),
            "questions_count": to_int(pick(p, "questions_count")),
            "is_inactive": p.get("status") != "marketable",
        },
    )


class DigikalaScraper(Scraper):
    name = "digikala"
    label = "دیجی‌کالا"
    hosts = ("digikala.com",)

    async def discover(self, client: httpx.AsyncClient, req: DiscoverRequest) -> list[Product]:
        out: list[Product] = []
        sort = SORTS.get(req.sort, 7)
        is_query = not re.fullmatch(r"[A-Za-z0-9_\-]+", req.category)  # فارسی/فاصله → جستجوی متنی
        for page in range(1, req.pages + 1):
            if is_query:
                data = await self.get_json(client, f"{BASE}/v1/search/", q=req.category,
                                           page=page, sort=sort)
            else:
                data = await self.get_json(
                    client, f"{BASE}/v1/categories/{req.category}/search/", page=page, sort=sort)
            items = pick(data, "data.products", default=[])
            out += [parse_listing_item(p) for p in items if p.get("id")]
            if page >= (to_int(pick(data, "data.pager.total_pages")) or 1):
                break
        return out

    async def product(self, client: httpx.AsyncClient, url: str) -> Product:
        m = re.search(r"dkp-(\d+)", url)
        if not m:
            raise ValueError("شناسه‌ی محصول دیجی‌کالا (dkp-...) در لینک پیدا نشد")
        data = await self.get_json(client, f"{BASE}/v2/product/{m.group(1)}/")
        return parse_product_detail(data, url)

    async def search(self, client: httpx.AsyncClient, query: str, limit: int = 10) -> list[Product]:
        data = await self.get_json(client, f"{BASE}/v1/search/", q=query)
        items = pick(data, "data.products", default=[])
        return [parse_listing_item(p) for p in items[:limit] if p.get("id")]
