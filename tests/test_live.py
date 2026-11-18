"""Live tests: hit the real ÖSYM site (no key, read-only).

Kept small and polite (~0.5s between requests, one call per tool).
Assertions are date-independent (counts and shapes, not frozen dates —
except the current-year list, which must contain 2026 items).

Run with:  python -m pytest tests/test_live.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from osym_mcp.server import (  # noqa: E402
    osym_exam_calendar,
    osym_exam_group,
    osym_get_announcement,
    osym_health,
    osym_latest_announcements,
    osym_search_announcements,
)


def _parse(out: str) -> dict:
    return json.loads(out)


def test_live_latest_announcements():
    out = _parse(osym_latest_announcements(limit=5))
    assert "error" not in out, out.get("error")
    assert out["count"] == 5
    assert out["total_on_page"] >= 100
    first = out["announcements"][0]
    assert first["date"] and first["date"].endswith(".2026")
    assert first["slug"] and first["url"].startswith("https://www.osym.gov.tr/")


def test_live_latest_year_2025():
    out = _parse(osym_latest_announcements(limit=3, year=2025))
    assert "error" not in out, out.get("error")
    assert out["count"] == 3
    assert all(a["date"].endswith(".2025") for a in out["announcements"])


def test_live_search_kpss():
    out = _parse(osym_search_announcements("KPSS", limit=5))
    assert "error" not in out, out.get("error")
    assert out["count"] >= 1
    assert all("kpss" in a["title"].lower() for a in out["announcements"])


def test_live_get_announcement():
    latest = _parse(osym_latest_announcements(limit=1))
    slug = latest["announcements"][0]["slug"]
    out = _parse(osym_get_announcement(slug))
    assert "error" not in out, out.get("error")
    assert out["title"]
    assert out["body"] and len(out["body"]) > 50
    assert out["url"].endswith(slug)


def test_live_calendar():
    out = _parse(osym_exam_calendar())
    assert "error" not in out, out.get("error")
    assert out["count"] >= 50
    shorts = {e["exam_short"] for e in out["exams"]}
    assert {"YKS", "KPSS", "ALES", "YDS", "DGS"} <= shorts
    yks = [e for e in out["exams"] if e["exam_short"] == "YKS"]
    assert yks and "Yükseköğretim" in yks[0]["exam_name"]


def test_live_calendar_query():
    out = _parse(osym_exam_calendar(query="yks"))
    assert "error" not in out, out.get("error")
    assert out["count"] >= 1
    assert all("yks" in e["exam_name"].lower() for e in out["exams"])


def test_live_exam_group_list():
    out = _parse(osym_exam_group())
    assert "error" not in out, out.get("error")
    assert out["count"] >= 30
    assert any(g["code"] == "yks" for g in out["groups"])


def test_live_exam_group_yks():
    out = _parse(osym_exam_group("yks", limit=3))
    assert "error" not in out, out.get("error")
    assert out["group_id"] == 2
    assert out["count"] >= 1
    assert "YKS" in (out["group_name"] or "")


def test_live_health():
    out = _parse(osym_health())
    assert out["status"] == "ok", out
    assert out["http_status"] == 200
