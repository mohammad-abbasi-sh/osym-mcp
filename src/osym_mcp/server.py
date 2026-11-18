"""MCP server: unofficial read-only access to ÖSYM (Turkish national exams)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import parse as _P

mcp = FastMCP("osym-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for ÖSYM (T.C. Ölçme, Seçme ve \
Yerleştirme Merkezi) — Türkiye's national exam authority: the \
announcements index (476 announcements in 2026 as of 18 Nov 2026, \
searchable per year back to 2010), full announcement texts with their \
guide PDFs, the official exam calendar (95 exams: YKS, KPSS, ALES, \
TUS, YDS, DGS, e-YDS, e-TEP and ~30 more groups, with application / \
late-application / exam / result / preference dates), and per-group \
announcement lists. Data comes from www.osym.gov.tr (server-rendered \
pages) — no login, no API key. Personal results live behind a login \
at sonuc.osym.gov.tr / ais.osym.gov.tr and are NOT covered: this \
server only exposes the public announcements, calendar and group \
pages. Search is Turkish-insensitive ("kpss" finds "KPSS"). \
Read-only; transport uses Chrome TLS impersonation with a \
plain-requests fallback; requests are spaced ~0.5s apart. Built by \
Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · \
https://mabbasi.ir — Turkey MCP factory.\
"""

_SOURCE = "www.osym.gov.tr"
_DISCLAIMER = (
    "Unofficial read-only ÖSYM data from the public pages of "
    "www.osym.gov.tr; verify dates on the official site before acting "
    "on them. Personal exam results are login-gated and not covered."
)


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


def _validate_limit(limit: int, lo: int, hi: int) -> int:
    if not lo <= limit <= hi:
        raise ValueError(f"limit must be between {lo} and {hi}")
    return limit


@mcp.tool()
def osym_latest_announcements(limit: int = 10, year: int | None = None) -> str:
    """The newest ÖSYM announcements, newest first.

    limit 1..50 (default 10). year: a calendar year (2010..2026) —
    the index page serves one year at a time; omit it for the current
    year. Returns title, date (DD.MM.YYYY), slug and URL per item.
    Use osym_get_announcement with the slug for the full text."""
    try:
        _validate_limit(limit, 1, 50)
        if year is not None and not 2010 <= year <= 2026:
            raise ValueError("year must be between 2010 and 2026")
        page = _http.fetch_announcements_page(year)
        items = _P.parse_announcement_list(page)
        return _ok({
            "year": year or "current",
            "count": len(items[:limit]),
            "total_on_page": len(items),
            "announcements": items[:limit],
        })
    except (ValueError, _http.OsymError) as e:
        return _err(e)


@mcp.tool()
def osym_search_announcements(query: str, year: int | None = None,
                              limit: int = 10) -> str:
    """Search ÖSYM announcements by title (Turkish-insensitive:
    "kpss" finds "KPSS", "sonuc" finds "sonuç").

    query: the search text. year: a calendar year (2010..2026) or
    omit for the current year. limit 1..50 (default 10). Returns
    matching items newest first, with title, date, slug and URL."""
    try:
        _validate_limit(limit, 1, 50)
        if year is not None and not 2010 <= year <= 2026:
            raise ValueError("year must be between 2010 and 2026")
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        page = _http.fetch_announcements_page(year)
        items = _P.parse_announcement_list(page)
        found = _P.filter_announcements(items, query=query, limit=limit)
        return _ok({
            "query": query,
            "year": year or "current",
            "count": len(found),
            "announcements": found,
        })
    except (ValueError, _http.OsymError) as e:
        return _err(e)


@mcp.tool()
def osym_get_announcement(slug: str) -> str:
    """The full text of one ÖSYM announcement.

    slug: the announcement slug from osym_latest_announcements /
    osym_search_announcements (e.g. "2026-kpss-on-lisans-sinavi-
    brans-bazinda-siralamalar"), or a full osym.gov.tr URL. Returns
    title, date, body text and links (guide PDFs on dokuman.osym.gov.tr
    first)."""
    try:
        slug = (slug or "").strip()
        if not slug:
            raise ValueError("slug must not be empty")
        if slug.startswith("http"):
            slug = slug.split("osym.gov.tr/", 1)[-1]
        page = _http.fetch_announcement_page(slug)
        detail = _P.parse_announcement_detail(page, f"{_P.BASE}/{slug.lstrip('/')}")
        if not detail["title"] and not detail["body"]:
            raise _http.OsymError(
                f"no announcement content found at {slug!r} — "
                "check the slug from osym_latest_announcements"
            )
        return _ok(detail)
    except (ValueError, _http.OsymError) as e:
        return _err(e)


@mcp.tool()
def osym_exam_calendar(query: str | None = None,
                       upcoming_only: bool = False) -> str:
    """ÖSYM's official exam calendar (Sınav Takvimi): all exams of the
    current year with pre-application, application, late-application,
    exam, pre-application-result, result and preference dates.

    query: optional Turkish-insensitive filter on the exam name/code
    (e.g. "yks", "kpss", "e-yds"). upcoming_only: keep only exams
    whose exam date is today or later. Returns one row per exam;
    "-" dates (not applicable) are null, and date ranges that run
    together on the site are kept verbatim."""
    try:
        page = _http.fetch_calendar_page()
        rows = _P.parse_calendar(page)
        if not rows:
            raise _http.OsymError("exam calendar table not found on the page")
        rows = _P.filter_calendar(rows, query=query, upcoming_only=upcoming_only)
        return _ok({
            "count": len(rows),
            "exams": rows,
        })
    except (ValueError, _http.OsymError) as e:
        return _err(e)


@mcp.tool()
def osym_exam_group(group: str | None = None, limit: int = 10) -> str:
    """Announcements of one ÖSYM exam group, newest first — or the
    full group list when called with no argument.

    group: a code ("yks", "kpss", "ales", "tus", "yds", "dgs",
    "e-yds", "e-tep", "yökdil", "tr-yös", "msü", "guy", ...), a full
    name ("Kamu Personel Seçme Sınavı") or a numeric id ("3").
    limit 1..50 (default 10). Returns the group name + its
    announcements (title, date, slug, URL)."""
    try:
        _validate_limit(limit, 1, 50)
        if group is None or not str(group).strip():
            return _ok({"count": len(_P.list_groups()), "groups": _P.list_groups()})
        gid, code = _P.resolve_group(str(group))
        page = _http.fetch_group_page(gid)
        title = _P.parse_group_title(page)
        items = _P.parse_announcement_list(page)
        return _ok({
            "group_id": gid,
            "group_code": code,
            "group_name": title,
            "count": len(items[:limit]),
            "total_on_page": len(items),
            "announcements": items[:limit],
        })
    except (ValueError, _http.OsymError) as e:
        return _err(e)


@mcp.tool()
def osym_health() -> str:
    """Check whether ÖSYM's site is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    Two polite requests; it does not fetch any announcements."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    import sys

    sys.exit(main())
