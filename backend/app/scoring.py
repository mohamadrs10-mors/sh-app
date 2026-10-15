"""امتیازدهی ساده و شفاف: تقاضا (نماینده‌ی فروش) + رقابت کم + رضایت مشتری.

هیچ سایتی آمار فروش واقعی نمی‌دهد (جز گاهی باسلام)؛ پس «تعداد نظرات/امتیازها»
به‌عنوان نماینده‌ی فروش استفاده می‌شود و در خروجی هم همین‌طور برچسب می‌خورد.
"""
from __future__ import annotations

import math

from .models import Product


def demand_signal(p: Product) -> int:
    return p.sold_count or p.rating_count or 0


def score_products(products: list[Product]) -> list[Product]:
    if not products:
        return products
    top = max(math.log1p(demand_signal(p)) for p in products) or 1.0
    for p in products:
        demand = math.log1p(demand_signal(p)) / top  # 0..1
        p.demand_score = round(100 * demand, 1)

        # رقابت: هرچه فروشنده‌ی کمتر، فرصت بیشتر (اگر نامعلوم، خنثی)
        if p.seller_count is None:
            competition = 0.5
        else:
            competition = 1 / (1 + math.log1p(max(p.seller_count - 1, 0)))
        rating = ((p.rating or 3.5) / 5) if p.rating is None or p.rating <= 5 else 0.7
        p.opportunity_score = round(100 * (0.6 * demand + 0.25 * competition + 0.15 * rating), 1)
    return sorted(products, key=lambda p: p.opportunity_score, reverse=True)
