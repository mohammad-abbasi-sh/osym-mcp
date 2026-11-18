"""HTTP layer for osym_mcp.

Data source: the Student Selection and Placement Centre (ÖSYM),
https://www.osym.gov.tr — the official Turkish national exam authority
(YKS, KPSS, ALES, TUS, YDS, DGS, e-YDS, e-TEP and ~30 more exam groups).
No login, no API key. Everything used here was verified live 2026-11-18:

- GET /Duyurular/Index — the current year's announcements, server-rendered,
  476 items on 2026-11-18 (1 Jan – 16 Nov 2026). Each item is
  ``<a class="duyuru-list-item" href="/<slug>" data-search-text="Title
  DD.MM.YYYY DD Month YYYY">`` — title + date in one attribute; the
  site's own search/filter is client-side over this list.
- GET /Duyurular/Index/{year} — that year's announcements (e.g. /2025
  returns 507 items from 2025 + 1 boundary item from 2024; /2024 returns
  542 from 2024 + 1 from 2025). The bare /Duyurular/Index always serves
  the current year.
- GET /<slug> — one announcement, server-rendered. The article body is
  Word-pasted HTML inside ``<div class="row content"><div
  class="col-sm-9">`` (title heading + <p> paragraphs + links to
  dokuman.osym.gov.tr PDFs); the sidebar lives in the sibling
  ``col-sm-3`` div and is excluded. The <title> tag carries the title;
  the ``<meta name="description">`` is truncated (~160 chars) and is NOT
  used for the body.
- GET /Sayfa/SinavTakvimi — the exam calendar, server-rendered: one
  <table> with 95 rows on 2026-11-18, columns Sınav Adı | Ön Başvuru
  Tarihi | Başvuru Tarihi | Geç Başvuru Tarihi | Sınav Tarihi | Ön
  Başvurunun Sonuç Tarihi | Sonuç Tarihi | Tercih Tarihleri. Cells hold
  "-" when a date does not apply; date ranges run together
  ("07.01.2026 14:0015.01.2026 23:59") and are kept verbatim.
- GET /SinavGrubu/Index/{id} — one exam group's announcements, same
  duyuru-list-item markup as /Duyurular/Index (e-TEP = id 1, 18 items
  on 2026-11-18). The <title> tag carries the group name
  ("e-TEP : Elektronik İngilizce Yeterlik Sınavı | ...").
  Group ids were taken from the site's own navigation on 2026-11-18
  (see EXAM_GROUPS in parse.py).

Personal results live behind a login at sonuc.osym.gov.tr / ais.osym.gov.tr
and are NOT covered — this server only exposes the public announcements,
calendar and group pages.

Transport uses curl-cffi Chrome impersonation with a plain-requests
fallback (the proven Turkey-factory pattern), even though the site
currently answers plain HTTP 200. Requests are kept gentle (one at a
time, ~0.5s apart) and read-only.
"""
from __future__ import annotations

import time

from curl_cffi import requests as _creq
import requests as _plain

BASE = "https://www.osym.gov.tr"
TIMEOUT = 30.0
MIN_INTERVAL = 0.5  # seconds between requests — be polite

_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_last_fetch = 0.0


class OsymError(RuntimeError):
    pass


def _throttle() -> None:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    _last_fetch = time.monotonic()


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, headers: dict, timeout: float = TIMEOUT):
    """GET with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process), retries
    once with the next profile on HTTP 403/429 or a transport error, then
    returns the last response (so the caller raises the specific 403/429
    error) or raises a network error if every attempt failed at the
    transport.
    """
    global _profile_idx
    last_exc: Exception | None = None
    for k in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + k) % len(_PROFILES)]
        try:
            resp = _creq.get(url, impersonate=profile, headers=headers, timeout=timeout)
        except Exception as e:
            last_exc = e
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            raise OsymError(f"network error fetching {url}: {e}") from e
        if resp.status_code in (403, 429):
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            return resp
        _profile_idx = (_profile_idx + k) % len(_PROFILES)
        return resp
    raise OsymError(f"network error fetching {url}: {last_exc}") from last_exc


def _get_text(url: str) -> str:
    """GET a URL, return the decoded text body.

    Raises OsymError with a human-readable message for HTTP errors.
    """
    _throttle()
    headers = dict(_HEADERS)
    try:
        resp = _request(url, headers)
        status, text = resp.status_code, resp.text
    except Exception:
        # Fallback transport: plain requests with a browser UA.
        try:
            resp = _plain.get(url, headers={**headers, "User-Agent": _UA}, timeout=TIMEOUT)
            status, text = resp.status_code, resp.text
        except OsymError:
            raise
        except Exception as e:
            raise OsymError(f"network error fetching {url}: {e}") from e
    if status == 403:
        raise OsymError(
            "www.osym.gov.tr refused the request (HTTP 403, bot wall)"
            " — try again later"
        )
    if status == 429:
        raise OsymError(
            "www.osym.gov.tr rate-limited the request (HTTP 429)"
            " — try again later"
        )
    if status == 404:
        raise OsymError(f"www.osym.gov.tr has no page at {url} (HTTP 404)")
    if status != 200:
        raise OsymError(
            f"www.osym.gov.tr returned HTTP {status} for {url}"
        )
    return text


def fetch_announcements_page(year: int | None = None) -> str:
    """The announcements index — current year, or one given year."""
    url = f"{BASE}/Duyurular/Index"
    if year is not None:
        url += f"/{year}"
    return _get_text(url)


def fetch_announcement_page(slug: str) -> str:
    """One announcement detail page. slug: the path after the domain,
    with or without a leading slash (e.g. "2026-kpss-...")."""
    slug = slug.lstrip("/")
    return _get_text(f"{BASE}/{slug}")


def fetch_calendar_page() -> str:
    """The exam calendar page (Sınav Takvimi)."""
    return _get_text(f"{BASE}/Sayfa/SinavTakvimi")


def fetch_group_page(group_id: int) -> str:
    """One exam group's announcements page."""
    return _get_text(f"{BASE}/SinavGrubu/Index/{group_id}")


def fetch_home_page() -> str:
    """The ÖSYM home page (used by the health check)."""
    return _get_text(f"{BASE}/")


def health_check() -> dict:
    """Two polite probes: the home page and the exam calendar.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `osym_health` tool
    and the daily smoke CI.
    """
    url = f"{BASE}/"
    try:
        import html as _html

        home = _html.unescape(fetch_home_page())
        if "ÖSYM" not in home and "Ölçme" not in home:
            return {
                "status": "error",
                "http_status": 200,
                "url": url,
                "detail": "home page returned 200 but no ÖSYM content",
            }
        cal = _html.unescape(fetch_calendar_page())
        if "Sınav Takvimi" not in cal:
            return {
                "status": "error",
                "http_status": 200,
                "url": f"{BASE}/Sayfa/SinavTakvimi",
                "detail": "calendar page returned 200 but no calendar content",
            }
    except OsymError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
