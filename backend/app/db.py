from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

from .models import Product

DB_PATH = Path(os.environ.get("SHAPP_DB", Path.home() / ".sh-app" / "data.db"))


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute(
        """CREATE TABLE IF NOT EXISTS products(
             source TEXT, source_id TEXT, data TEXT, saved INTEGER DEFAULT 0,
             updated REAL, PRIMARY KEY(source, source_id))"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS history(
             source TEXT, source_id TEXT, ts REAL, price INTEGER, rating_count INTEGER)"""
    )
    return c


def upsert(products: list[Product]) -> None:
    now = time.time()
    with _conn() as c:
        for p in products:
            c.execute(
                """INSERT INTO products(source, source_id, data, updated) VALUES(?,?,?,?)
                   ON CONFLICT(source, source_id) DO UPDATE SET data=excluded.data, updated=excluded.updated""",
                (p.source, p.source_id, p.model_dump_json(), now),
            )
            c.execute("INSERT INTO history VALUES(?,?,?,?,?)",
                      (p.source, p.source_id, now, p.price, p.rating_count))


def set_saved(source: str, source_id: str, saved: bool) -> None:
    with _conn() as c:
        c.execute("UPDATE products SET saved=? WHERE source=? AND source_id=?",
                  (int(saved), source, source_id))


def saved_products() -> list[Product]:
    with _conn() as c:
        rows = c.execute("SELECT data FROM products WHERE saved=1 ORDER BY updated DESC").fetchall()
    return [Product.model_validate(json.loads(r[0])) for r in rows]


def history(source: str, source_id: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT ts, price, rating_count FROM history WHERE source=? AND source_id=? ORDER BY ts",
            (source, source_id)).fetchall()
    return [{"ts": r[0], "price": r[1], "rating_count": r[2]} for r in rows]
