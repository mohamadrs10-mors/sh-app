from __future__ import annotations

from pydantic import BaseModel, Field


class Seller(BaseModel):
    name: str
    price: int | None = None  # تومان
    city: str | None = None
    url: str | None = None


class Product(BaseModel):
    source: str
    source_id: str
    title: str
    url: str
    image: str | None = None
    price: int | None = None  # تومان
    old_price: int | None = None
    discount_percent: int | None = None
    rating: float | None = None
    rating_count: int | None = None  # تعداد نظرات/امتیاز؛ نماینده‌ی فروش
    sold_count: int | None = None  # فقط اگر سایت مستقیم بدهد (مثلاً باسلام)
    seller_count: int | None = None
    brand: str | None = None
    category: str | None = None
    in_stock: bool | None = None
    sellers: list[Seller] = Field(default_factory=list)
    specs: dict[str, str] = Field(default_factory=dict)
    extra: dict = Field(default_factory=dict)  # هر چیز دیگری که سایت داده
    # خروجی تحلیل
    demand_score: float = 0
    opportunity_score: float = 0


class DiscoverRequest(BaseModel):
    source: str
    category: str = Field(description="اسلاگ دسته (دیجی‌کالا) یا عبارت جستجو (ترب/باسلام)")
    sort: str = "bestseller"  # bestseller | visits | newest | cheapest
    pages: int = Field(default=2, ge=1, le=10)
    min_price: int | None = None
    max_price: int | None = None


class AnalyzeRequest(BaseModel):
    url: str
    cross_search: bool = True  # همان محصول را در سایت‌های دیگر هم بگرد


class KeywordRequest(BaseModel):
    keyword: str
    sources: list[str] = Field(default_factory=lambda: ["digikala", "torob", "basalam"])
    sort: str = "bestseller"
    pages: int = Field(default=1, ge=1, le=5)  # صفحه برای هر عبارت
    terms: list[str] | None = None  # اگر داده شود به‌جای عبارت‌های گروه استفاده می‌شود
    min_price: int | None = None
    max_price: int | None = None


class KeywordGroup(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    terms: list[str]
