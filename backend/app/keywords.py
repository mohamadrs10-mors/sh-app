"""کلیدواژه → فهرست عبارت‌های جستجو. کاربر می‌تواند گروه‌ها را در برنامه ویرایش کند."""
from __future__ import annotations

import re

from . import config

DEFAULT_GROUPS = [
    {"name": "چوب", "aliases": ["چوب", "چوبی", "wood", "wooden", "تخته"],
     "terms": ["تخته چوب راش", "چوب بلوط", "چوب ماسیف", "ام دی اف", "ظرف چوبی", "جعبه چوبی",
               "میز چوبی", "قفسه چوبی", "جاکلیدی چوبی", "اسباب بازی چوبی", "تابلو چوبی",
               "سینی چوبی", "تخته برش چوبی", "لوازم چوبی آشپزخانه", "چوب طبیعی"]},
    {"name": "موبایل", "aliases": ["گوشی", "موبایل", "تلفن همراه", "mobile", "phone"],
     "terms": ["گوشی موبایل", "قاب گوشی", "گلس گوشی", "شارژر گوشی", "هندزفری", "پاوربانک",
               "هولدر گوشی", "کابل شارژ", "ساعت هوشمند", "اسپیکر بلوتوث"]},
    {"name": "آشپزخانه", "aliases": ["آشپزخانه", "اشپزخانه", "kitchen"],
     "terms": ["لوازم آشپزخانه", "ظروف آشپزخانه", "قاشق چنگال", "تخته گوشت", "سینی", "جا ادویه"]},
    {"name": "اسباب بازی", "aliases": ["اسباب بازی", "اسباب‌بازی", "بازی کودک", "toy"],
     "terms": ["اسباب بازی چوبی", "پازل", "بازی فکری", "عروسک", "ماشین اسباب بازی"]},
]


def norm(s: str) -> str:
    s = s.replace("ي", "ی").replace("ك", "ک").replace("‌", " ").replace("‌", " ")
    return re.sub(r"\s+", " ", s).strip().lower()


def groups() -> list[dict]:
    custom = config.load().get("keyword_groups")
    return custom if isinstance(custom, list) and custom else DEFAULT_GROUPS


def save_groups(gs: list[dict]) -> None:
    clean = []
    for g in gs:
        name = str(g.get("name", "")).strip()
        terms = [t.strip() for t in g.get("terms", []) if str(t).strip()]
        aliases = [a.strip() for a in g.get("aliases", []) if str(a).strip()]
        if name and terms:
            clean.append({"name": name, "aliases": aliases, "terms": terms})
    config.save({**config.load(), "keyword_groups": clean})


def reset_groups() -> None:
    cfg = config.load()
    cfg.pop("keyword_groups", None)
    config.save(cfg)


def resolve(keyword: str) -> tuple[str | None, list[str]]:
    """(نام گروه، عبارت‌ها). اگر گروهی نخورد، خود کلیدواژه تنها عبارت است."""
    k = norm(keyword)
    if not k:
        return None, []
    best = None
    for g in groups():
        names = [norm(g["name"])] + [norm(a) for a in g.get("aliases", [])]
        if k in names:
            return g["name"], list(g["terms"])
        if best is None and any(len(n) >= 3 and (n in k or k in n) for n in names):
            best = g
    if best:
        return best["name"], list(best["terms"])
    return None, [keyword.strip()]
