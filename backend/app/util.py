from __future__ import annotations

import re
from typing import Any

_FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def digits(s: str) -> str:
    return s.translate(_FA)


def to_int(v: Any) -> int | None:
    """عدد را از int/float/متن فارسی و انگلیسی استخراج می‌کند."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    m = re.sub(r"[^\d.]", "", digits(str(v)).replace(",", "").replace("٬", ""))
    try:
        return int(float(m)) if m else None
    except ValueError:
        return None


def to_float(v: Any) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return float(digits(str(v)))
    except ValueError:
        return None


def pick(d: Any, *paths: str, default: Any = None) -> Any:
    """اولین مسیر نقطه‌دار که مقدار غیرخالی داشته باشد (برای APIهای ناپایدار)."""
    for path in paths:
        cur = d
        for key in path.split("."):
            if isinstance(cur, dict):
                cur = cur.get(key)
            elif isinstance(cur, list) and key.isdigit() and int(key) < len(cur):
                cur = cur[int(key)]
            else:
                cur = None
            if cur is None:
                break
        if cur not in (None, "", [], {}):
            return cur
    return default
