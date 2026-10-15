import os, tempfile
os.environ["SHAPP_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")

from fastapi.testclient import TestClient

from app.main import app
from app.scoring import score_products
from app.scrapers.basalam import parse_item
from app.scrapers.digikala import parse_listing_item, parse_product_detail
from app.scrapers.torob import parse_details, parse_result
from app.util import to_int

DK = {"id": 123, "title_fa": "تخته چوب راش", "url": {"uri": "/product/dkp-123/x/"},
      "images": {"main": {"url": ["http://i/1.jpg"]}}, "status": "marketable",
      "default_variant": {"price": {"selling_price": 5000000, "rrp_price": 6000000,
                                    "discount_percent": 17}, "seller": {"title": "ف"}},
      "rating": {"rate": 4.6, "count": 320}, "data_layer": {"brand": "ب", "category": "چوب"}}


def test_to_int():
    assert to_int("۱۲٬۵۰۰ تومان") == 12500
    assert to_int(None) is None


def test_digikala_listing_converts_rial_to_toman():
    p = parse_listing_item(DK)
    assert p.price == 500000 and p.old_price == 600000
    assert p.rating_count == 320 and p.url.endswith("/dkp-123/x/")


def test_digikala_detail():
    d = {"data": {"product": {"id": 123, "title_fa": "ت", "status": "marketable",
         "rating": {"rate": 4, "count": 9},
         "variants": [{"price": {"selling_price": 20000}, "seller": {"title": "الف"}},
                      {"price": {"selling_price": 30000}, "seller": {"title": "ب"}}],
         "specifications": [{"attributes": [{"title": "جنس", "values": ["راش"]}]}]}}}
    p = parse_product_detail(d, "u")
    assert p.seller_count == 2 and p.price == 2000 and p.specs == {"جنس": "راش"}


def test_torob():
    p = parse_result({"random_key": "abc-123", "name1": "چوب", "price": 90000, "shop_text": "۱۲ فروشگاه"})
    assert p.seller_count == 12 and p.price == 90000
    d = parse_details({"base_product": {"random_key": "k", "name1": "n"},
                       "products_info": {"result": [{"shop_name": "a", "price": 100},
                                                    {"shop_name": "b", "price": 150}]}}, "u")
    assert d.price == 100 and d.extra["price_spread_pct"] == 33


def test_basalam():
    p = parse_item({"id": 5, "name": "تخته", "price": 1000000, "vendor": {"identifier": "shop1"},
                    "rating": {"average": 4.8, "count": 40}, "soldCount": 200})
    assert p.url == "https://basalam.com/shop1/product/5" and p.price == 100000
    assert p.sold_count == 200 and p.rating == 4.8


def test_scoring_prefers_demand():
    a, b = parse_listing_item(DK), parse_listing_item({**DK, "id": 9, "rating": {"rate": 4, "count": 2}})
    r = score_products([b, a])
    assert r[0].source_id == "123"


def test_api_basics():
    c = TestClient(app)
    assert c.get("/health").json() == {"ok": True, "app": "shapp"}
    assert len(c.get("/api/sources").json()) == 3
    assert c.post("/api/analyze", json={"url": "https://example.com/x"}).status_code == 400


def test_web_ui_served():
    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200 and "یابنده" in r.text
    assert c.get("/api/config").json()["lan_url"].startswith("http://")


def test_dashboard_endpoints():
    c = TestClient(app)
    assert c.get("/api/ping").json()["ok"]
    s = c.get("/api/stats").json()
    assert {"total", "saved", "by_source", "top"} <= s.keys()
    assert isinstance(c.get("/api/products").json(), list)


def test_keyword_resolve_and_discover(monkeypatch):
    from app import keywords
    assert keywords.resolve("چوبی")[0] == "چوب"
    assert keywords.resolve("گوشی")[0] == "موبایل"
    assert keywords.resolve("كتاب") == (None, ["كتاب"])  # نامعلوم: خودش عبارت می‌شود

    from app.scrapers import REGISTRY

    async def fake(self, client, req):
        if req.category == "ام دی اف" and self.name == "torob":
            raise RuntimeError("boom")
        p = parse_listing_item({**DK, "id": abs(hash(req.category)) % 10**6})
        p.source = self.name
        return [p, parse_listing_item(DK)]  # DK تکراری باید ادغام شود

    for s in REGISTRY.values():
        monkeypatch.setattr(type(s), "discover", fake)
    c = TestClient(app)
    r = c.post("/api/discover_keyword", json={"keyword": "چوب", "sources": ["digikala", "torob"],
                                              "terms": ["تخته", "ام دی اف"]}).json()
    assert r["group"] == "چوب"
    assert len(r["errors"]) == 1 and "ام دی اف" in r["errors"][0]
    keys = {(p["source"], p["source_id"]) for p in r["products"]}
    assert len(keys) == len(r["products"])  # بدون تکراری
    assert r["products"][0]["opportunity_score"] >= r["products"][-1]["opportunity_score"]


def test_keywords_crud():
    c = TestClient(app)
    gs = c.get("/api/keywords").json()
    assert any(g["name"] == "چوب" for g in gs)
    c.put("/api/keywords", json=[{"name": "تست", "aliases": ["t"], "terms": ["الف", "ب"]}])
    assert c.get("/api/keywords/resolve", params={"q": "t"}).json()["terms"] == ["الف", "ب"]
    assert c.post("/api/keywords/reset").json()[0]["name"] == "چوب"
