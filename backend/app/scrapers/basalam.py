from __future__ import annotations

import re

import httpx

from ..models import DiscoverRequest, Product
from ..util import pick, to_float, to_int
from .base import Scraper

SEARCH = "https://search.basalam.com/ai-engine/api/v2.0/product/search"
CORE = "https://core.basalam.com/api_v2/product"
SORTS = {"bestseller": "sales", "visits": "visit", "newest": "newest", "cheapest": "cheapest"}


def _price(v) -> int | None:
    """باسلام قیمت را به ریال می‌دهد."""
    n = to_int(v)
    return n // 10 if n is not None else None


def parse_item(p: dict) -> Product:
    pid = str(p.get("id"))
    vendor = pick(p, "vendor.identifier", "vendor.id", default="")
    price = _price(pick(p, "price"))
    old = _price(pick(p, "primaryPrice", "primary_price"))
    return Product(
        source="basalam",
        source_id=pid,
        title=p.get("name") or p.get("title") or "",
        url=f"https://basalam.com/{vendor}/product/{pid}",
        image=pick(p, "photo.MEDIUM", "photo.LARGE", "photo.url", "photo.md"),
        price=price,
        old_price=old if old and price and old > price else None,
        discount_percent=to_int(pick(p, "discountPercent", "discount_percent")),
        rating=to_float(pick(p, "rating.average", "rating.rating")),
        rating_count=to_int(pick(p, "rating.count", "rating.total", "reviewCount")),
        sold_count=to_int(pick(p, "soldCount", "sold_count", "sales_count", "stats.sold")),
        category=pick(p, "category.title", "categoryTitle"),
        in_stock=(to_int(pick(p, "inventory", "stock")) or 1) > 0,
        extra={
            "vendor": pick(p, "vendor.name"),
            "vendor_city": pick(p, "vendor.city.title", "vendor.city"),
            "vendor_score": to_float(pick(p, "vendor.score", "vendor.rating")),
            "preparation_days": to_int(pick(p, "preparationDays", "preparation_days")),
            "free_shipping": bool(pick(p, "freeShipping", "has_free_shipping")),
        },
    )


class BasalamScraper(Scraper):
    name = "basalam"
    label = "باسلام"
    hosts = ("basalam.com",)

    async def discover(self, client: httpx.AsyncClient, req: DiscoverRequest) -> list[Product]:
        out: list[Product] = []
        rows = 48
        for page in range(req.pages):
            data = await self.get_json(
                client, SEARCH, q=req.category, **{"from": page * rows}, rows=rows,
                **{"filters.sort": SORTS.get(req.sort, "sales")},
            )
            items = data.get("products") or []
            if not items:
                break
            out += [parse_item(p) for p in items if p.get("id")]
        return out

    async def product(self, client: httpx.AsyncClient, url: str) -> Product:
        m = re.search(r"/product/(\d+)", url)
        if not m:
            raise ValueError("شناسه‌ی محصول باسلام (/product/...) در لینک پیدا نشد")
        data = await self.get_json(client, f"{CORE}/{m.group(1)}")
        prod = parse_item(data)
        prod.url = url
        prod.specs = {
            str(a.get("title")): str(a.get("value") or ", ".join(
                v.get("title", "") for v in a.get("values", [])))
            for a in (data.get("attributes") or []) if a.get("title")
        }
        prod.extra["description"] = (data.get("description") or "")[:1500]
        prod.extra["weight_g"] = to_int(data.get("weight"))
        return prod

    async def search(self, client: httpx.AsyncClient, query: str, limit: int = 10) -> list[Product]:
        data = await self.get_json(client, SEARCH, q=query, rows=limit)
        return [parse_item(p) for p in (data.get("products") or [])[:limit] if p.get("id")]
