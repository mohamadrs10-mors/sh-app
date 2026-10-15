from __future__ import annotations

import re
from urllib.parse import unquote

import httpx

from ..models import DiscoverRequest, Product, Seller
from ..util import pick, to_int
from .base import Scraper

BASE = "https://api.torob.com"
SORTS = {"bestseller": "popularity", "visits": "popularity", "newest": "date", "cheapest": "price"}


def parse_result(r: dict) -> Product:
    prk = str(r.get("random_key") or "")
    price = to_int(r.get("price"))
    shops = to_int(pick(r, "shop_text")) or to_int(r.get("shop_count"))
    url = r.get("web_client_absolute_url") or f"https://torob.com/p/{prk}/"
    return Product(
        source="torob",
        source_id=prk,
        title=r.get("name1") or r.get("name2") or "",
        url=url,
        image=r.get("image_url"),
        price=price,
        seller_count=shops,
        extra={"price_text": r.get("price_text"), "shop_text": r.get("shop_text"),
               "subtitle": r.get("name2")},
    )


def parse_details(data: dict, url: str) -> Product:
    base = data.get("base_product") or data
    prk = str(pick(base, "random_key", default=""))
    sellers = []
    for s in pick(data, "products_info.result", "products", default=[]) or []:
        sellers.append(Seller(
            name=pick(s, "shop_name", "shop.name", default="?"),
            price=to_int(s.get("price")),
            city=pick(s, "shop_city", "city"),
            url=pick(s, "page_url", "shop_url"),
        ))
    prices = [s.price for s in sellers if s.price]
    attrs = pick(data, "structural_specs", "attributes", default={}) or {}
    specs = {str(k): str(v) for k, v in attrs.items()} if isinstance(attrs, dict) else {}
    return Product(
        source="torob",
        source_id=prk,
        title=pick(base, "name1", "title", default=""),
        url=url,
        image=pick(base, "image_url", "image_urls.0"),
        price=min(prices) if prices else to_int(pick(base, "price")),
        seller_count=len(sellers) or to_int(base.get("shops_count")),
        category=pick(base, "category.title", "breadcrumbs.-1.title"),
        brand=pick(base, "brand.title"),
        sellers=sellers,
        specs=specs,
        extra={"max_price": max(prices) if prices else None,
               "price_spread_pct": round(100 * (max(prices) - min(prices)) / max(prices))
               if len(prices) > 1 and max(prices) else None},
    )


class TorobScraper(Scraper):
    name = "torob"
    label = "ترب"
    hosts = ("torob.com",)

    async def discover(self, client: httpx.AsyncClient, req: DiscoverRequest) -> list[Product]:
        out: list[Product] = []
        for page in range(req.pages):
            data = await self.get_json(
                client, f"{BASE}/v4/base-product/search/",
                query=req.category, page=page, size=24, sort=SORTS.get(req.sort, "popularity"),
            )
            results = data.get("results") or []
            if not results:
                break
            out += [parse_result(r) for r in results if r.get("random_key")]
        return out

    async def product(self, client: httpx.AsyncClient, url: str) -> Product:
        m = re.search(r"/p/([0-9a-f-]{8,})", unquote(url))
        if not m:
            raise ValueError("شناسه‌ی محصول ترب (/p/...) در لینک پیدا نشد")
        data = await self.get_json(client, f"{BASE}/v4/base-product/details/", prk=m.group(1))
        return parse_details(data, url)

    async def search(self, client: httpx.AsyncClient, query: str, limit: int = 10) -> list[Product]:
        data = await self.get_json(client, f"{BASE}/v4/base-product/search/", query=query, page=0)
        return [parse_result(r) for r in (data.get("results") or [])[:limit] if r.get("random_key")]
