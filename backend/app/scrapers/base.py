from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod

import httpx

from ..models import DiscoverRequest, Product

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.5",
}


class Scraper(ABC):
    name: str
    label: str
    hosts: tuple[str, ...]

    def matches_url(self, url: str) -> bool:
        return any(h in url for h in self.hosts)

    async def get_json(self, client: httpx.AsyncClient, url: str, **params) -> dict:
        """درخواست با تلاش مجدد و مکث تصادفی تا فشار کمتری به سایت بیاید."""
        last: Exception | None = None
        for attempt in range(3):
            try:
                await asyncio.sleep(random.uniform(0.3, 0.9))
                r = await client.get(url, params=params or None, headers=HEADERS, timeout=25)
                if r.status_code == 429:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                r.raise_for_status()
                return r.json()
            except (httpx.HTTPError, ValueError) as e:
                last = e
                await asyncio.sleep(1 + attempt)
        raise RuntimeError(f"{self.label}: دریافت اطلاعات ناموفق بود ({last})")

    @abstractmethod
    async def discover(self, client: httpx.AsyncClient, req: DiscoverRequest) -> list[Product]: ...

    @abstractmethod
    async def product(self, client: httpx.AsyncClient, url: str) -> Product: ...

    @abstractmethod
    async def search(self, client: httpx.AsyncClient, query: str, limit: int = 10) -> list[Product]: ...
