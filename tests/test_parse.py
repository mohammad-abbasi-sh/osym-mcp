"""Offline tests for osym_mcp parsers (recorded fixtures, no network).

Fixtures (recorded 2026-11-18 from www.osym.gov.tr):
- duyurular-2026.html — the announcements list fragment (476 items)
- takvim-table.html — the exam calendar table (95 rows)
- duyuru-detail.html — one announcement article column (KPSS rankings)
- grup-1.html — the e-TEP group announcements fragment (18 items)
- grup-1-title.txt — the e-TEP group page title

Run with:  python -m pytest tests/test_parse.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from osym_mcp import parse as P  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


# --- announcements list ----------------------------------------------------

def test_list_count_and_order():
    items = P.parse_announcement_list(_read("duyurular-2026.html"))
    assert len(items) == 476
    assert items[0]["date"] == "16.11.2026"
    assert items[0]["slug"] == "2026-guy2-sinava-giris-belgeleri-erisime-acildi"
    assert items[0]["url"] == (
        "https://www.osym.gov.tr/2026-guy2-sinava-giris-belgeleri-erisime-acildi"
    )
    assert "GUY/2" in items[0]["title"]
    # newest first
    assert items[0]["date"] >= items[-1]["date"]
    assert items[-1]["date"] == "01.01.2026"


def test_list_title_has_no_date_suffix():
    items = P.parse_announcement_list(_read("duyurular-2026.html"))
    for it in items[:20]:
        assert "Kasım 2026" not in it["title"], it["title"]
        assert it["date"] and len(it["date"]) == 10


def test_filter_by_query_turkish_insensitive():
    items = P.parse_announcement_list(_read("duyurular-2026.html"))
    kpss = P.filter_announcements(items, query="kpss", limit=50)
    assert kpss, "expected KPSS announcements"
    assert all("kpss" in P.normalize_tr(it["title"]) for it in kpss)
    # "sonuc" (no ç) must match "Sonuçları"
    sonuc = P.filter_announcements(items, query="sonuc", limit=50)
    assert sonuc
    assert all("sonuç" in P.normalize_tr(it["title"]) for it in sonuc)


def test_filter_by_year():
    items = P.parse_announcement_list(_read("duyurular-2026.html"))
    assert P.filter_announcements(items, year=2026, limit=50)
    assert P.filter_announcements(items, year=2025, limit=50) == []


def test_filter_limit():
    items = P.parse_announcement_list(_read("duyurular-2026.html"))
    assert len(P.filter_announcements(items, limit=5)) == 5


# --- one announcement ------------------------------------------------------

def test_detail_title_date_body():
    detail = P.parse_announcement_detail(
        _read("duyuru-detail.html"),
        "https://www.osym.gov.tr/2026-kpss-on-lisans-sinavi-brans-bazinda-siralamalar",
    )
    assert detail["title"] == (
        "2026 KPSS Ön Lisans Sınavı: Branş Bazında Sıralamalar"
    )
    assert detail["date"] == "12 Kasım 2026"
    assert "branş bazında sıralamaları" in detail["body"]
    assert "Adaylara ve kamuoyuna saygıyla duyurulur" in detail["body"]
    assert "ÖSYM BAŞKANLIĞI" in detail["body"]
    # sidebar must not leak in
    assert "Sayısal Bilgiler" not in detail["body"]
    assert "Kılavuzlar" not in detail["body"]
    # title must not be repeated as the first body line
    assert not detail["body"].startswith(detail["title"])


def test_detail_links_pdf_first():
    detail = P.parse_announcement_detail(
        _read("duyuru-detail.html"),
        "https://www.osym.gov.tr/2026-kpss-on-lisans-sinavi-brans-bazinda-siralamalar",
    )
    assert detail["links"], "expected links in the article"
    pdfs = [l for l in detail["links"] if l["url"].endswith(".pdf")]
    assert pdfs, "expected a dokuman.osym.gov.tr PDF link"
    assert detail["links"][0]["url"].endswith(".pdf")
    assert any("ais.osym.gov.tr" in l["url"] for l in detail["links"])


# --- exam calendar ----------------------------------------------------------

def test_calendar_row_count_and_header():
    rows = P.parse_calendar(_read("takvim-table.html"))
    assert len(rows) == 94  # 95 <tr> incl. the header row
    assert rows[0]["exam_short"] == "EKPSS"
    assert "Engelli Kamu Personeli" in rows[0]["exam_name"]


def test_calendar_columns_and_nulls():
    rows = P.parse_calendar(_read("takvim-table.html"))
    for r in rows:
        assert set(r) == {
            "exam_short", "exam_name", "pre_application_dates",
            "application_dates", "late_application_dates", "exam_date",
            "pre_application_result_date", "result_date",
            "preference_dates",
        }
    # first row has no dates at all ("-")
    assert rows[0]["application_dates"] is None
    assert rows[0]["exam_date"] is None
    # e-YDS row has a real application range
    eyds = [r for r in rows if r["exam_short"] == "e-YDS"]
    assert eyds
    assert eyds[0]["application_dates"] is not None
    assert "2026" in eyds[0]["application_dates"]


def test_calendar_filter_query():
    rows = P.parse_calendar(_read("takvim-table.html"))
    yks = P.filter_calendar(rows, query="yks")
    assert yks
    assert all("yks" in P.normalize_tr(r["exam_name"]) for r in yks)
    assert P.filter_calendar(rows, query="zzzz-no-such-exam") == []


# --- exam groups ------------------------------------------------------------

def test_group_title_and_items():
    title = P.parse_group_title(
        "<title>" + _read("grup-1-title.txt") + "</title>"
    )
    assert title and title.startswith("e-TEP")
    assert "Elektronik" in title
    page = _read("grup-1.html")
    items = P.parse_announcement_list(page)
    assert len(items) == 18
    assert all("e-TEP" in it["title"] or "TEP" in it["title"] for it in items[:5])


def test_resolve_group():
    assert P.resolve_group("yks") == (2, "yks")
    assert P.resolve_group("KPSS") == (3, "kpss")
    assert P.resolve_group("3") == (3, "kpss")
    assert P.resolve_group("Kamu Personel Seçme Sınavı") == (3, "kpss")
    assert P.resolve_group("e-yds") == (7, "e-yds")
    try:
        P.resolve_group("no-such-exam")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for unknown group")


def test_list_groups_unique_sorted():
    groups = P.list_groups()
    ids = [g["id"] for g in groups]
    assert ids == sorted(ids) and len(ids) == len(set(ids))
    assert any(g["code"] == "yks" and g["id"] == 2 for g in groups)
    assert any(g["code"] == "kpss" and g["id"] == 3 for g in groups)
    assert len(groups) >= 30
