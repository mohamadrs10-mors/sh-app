from .base import Scraper
from .basalam import BasalamScraper
from .digikala import DigikalaScraper
from .torob import TorobScraper

REGISTRY: dict[str, Scraper] = {
    s.name: s for s in (DigikalaScraper(), TorobScraper(), BasalamScraper())
}


def for_url(url: str) -> Scraper | None:
    return next((s for s in REGISTRY.values() if s.matches_url(url)), None)
