"""Parsers for ÖSYM's server-rendered pages (stdlib only).

All markup shapes were verified against live pages fetched 2026-11-18;
offline tests run against recorded fixtures in tests/fixtures/.
"""
from __future__ import annotations

import html as _html
import re

BASE = "https://www.osym.gov.tr"

# Exam groups, taken from the site's own navigation on 2026-11-18
# (short code -> (group id, full Turkish name)).
EXAM_GROUPS: dict[str, tuple[int, str]] = {
    "e-tep": (1, "Elektronik İngilizce Yeterlik Sınavı"),
    "yks": (2, "Yükseköğretim Kurumları Sınavı"),
    "kpss": (3, "Kamu Personel Seçme Sınavı"),
    "ekpss": (4, "Engelli Kamu Personeli Seçme Sınavı"),
    "ales": (5, "Akademik Personel ve Lisansüstü Eğitimi Giriş Sınavı"),
    "tus": (6, "Tıpta Uzmanlık Eğitimi Giriş Sınavı"),
    "yds": (7, "Yabancı Dil Bilgisi Seviye Tespit Sınavı"),
    "e-yds": (7, "Yabancı Dil Bilgisi Seviye Tespit Sınavı"),
    "dgs": (8, "Dikey Geçiş Sınavı"),
    "dus": (9, "Diş Hekimliği Uzmanlık Eğitimi Giriş Sınavı"),
    "ydus": (10, "Tıpta Yan Dal Uzmanlık Eğitimi Giriş Sınavı"),
    "eus": (11, "Eczacılıkta Uzmanlık Eğitimi Giriş Sınavı"),
    "yökdil": (12, "Yükseköğretim Kurumları Yabancı Dil Sınavı"),
    "e-yökdil": (12, "Yükseköğretim Kurumları Yabancı Dil Sınavı"),
    "tr-yös": (13, "TR-YÖS"),
    "meb-ags": (15, "MEB-AGS"),
    "bkubts": (16, "BKUBTS"),
    "özyes": (17, "ÖZYES"),
    "iyös": (18, "İYÖS"),
    "hmgs": (19, "HMGS"),
    "sts öğretmenlik": (21, "STS Öğretmenlik"),
    "sts eczacılık": (22, "STS Eczacılık"),
    "i̇cra": (24, "İCRA"),
    "meb-ekys": (25, "MEB-EKYS"),
    "msü": (27, "MSÜ"),
    "sayıştay yazılı": (29, "Sayıştay Yazılı"),
    "sayıştay eleme": (32, "Sayıştay Eleme"),
    "ydh": (34, "YDH"),
    "guy": (37, "GUY"),
    "mühendislik tamamlama": (38, "Mühendislik Tamamlama"),
    "sts diş hekimliği": (39, "STS Diş Hekimliği"),
    "sts tıp": (45, "STS Tıp"),
    "dib-mbsts": (47, "DİB-MBSTS"),
    "e-ydts": (54, "e-YDTS"),
    "yök-ykds": (56, "YÖK-YKDS"),
}

_TR_LOWER = str.maketrans({
    "İ": "i", "I": "ı", "Ş": "ş", "Ç": "ç", "Ğ": "ğ", "Ü": "ü", "Ö": "ö",
})


def normalize_tr(text: str) -> str:
    """Turkish-insensitive lowercase: İ/I, ş, ğ, ü, ö, ç, ı all fold,
    so "kpss", "KPSS" and "kpsş" behave the same and "ank" finds "ANKARA"."""
    return text.translate(_TR_LOWER).lower()


def _clean(text: str) -> str:
    """Unescape HTML entities and collapse whitespace."""
    text = _html.unescape(text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Announcements list (/Duyurular/Index[/year] and /SinavGrubu/Index/{id})
# ---------------------------------------------------------------------------

_LIST_ITEM_RE = re.compile(
    r'<a class="duyuru-list-item" href="([^"]+)"[^>]*'
    r'data-search-text="([^"]*)"',
    re.S,
)
# data-search-text = "Title DD.MM.YYYY DD Month YYYY"
_SEARCH_TEXT_RE = re.compile(
    r"^(.*?)\s+(\d{2}\.\d{2}\.\d{4})\s+\d{1,2}\s+\S+\s+\d{4}\s*$", re.S
)


def parse_announcement_list(page_html: str) -> list[dict]:
    """Parse every duyuru-list-item on an announcements index page.

    Returns [{"title", "date" (DD.MM.YYYY), "slug", "url"}] in page
    order (newest first). Items whose data-search-text has no date are
    kept with date None rather than dropped.
    """
    out: list[dict] = []
    for href, search_text in _LIST_ITEM_RE.findall(page_html):
        search_text = _clean(search_text)
        m = _SEARCH_TEXT_RE.match(search_text)
        if m:
            title, date = _clean(m.group(1)), m.group(2)
        else:
            title, date = search_text, None
        slug = href.lstrip("/")
        out.append({
            "title": title,
            "date": date,
            "slug": slug,
            "url": f"{BASE}/{slug}",
        })
    return out


def filter_announcements(items: list[dict], query: str | None = None,
                         year: int | None = None,
                         limit: int = 10) -> list[dict]:
    """Turkish-insensitive substring filter over titles (+ optional
    year filter on the DD.MM.YYYY date). Page order is preserved."""
    q = normalize_tr(query) if query else None
    out = []
    for it in items:
        if year is not None:
            if not it["date"] or not it["date"].endswith(f".{year}"):
                continue
        if q and q not in normalize_tr(it["title"]):
            continue
        out.append(it)
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# One announcement (/slug)
# ---------------------------------------------------------------------------

def _extract_col9(page_html: str) -> str:
    """The article column: <div ... class="col-sm-9"> ... up to the
    sibling col-sm-3 sidebar. Falls back to the whole page."""
    m = re.search(r'<div[^>]*class="col-sm-9"[^>]*>', page_html)
    if not m:
        return page_html
    start = m.end()
    end = page_html.find('class="col-sm-3"', start)
    if end == -1:
        end = len(page_html)
    # back up to the closing </div> of the col-sm-9 block
    close = page_html.rfind("</div>", start, end)
    return page_html[start:close if close != -1 else end]


def _html_to_text(fragment: str) -> str:
    """Strip tags from an HTML fragment, keeping paragraph breaks."""
    frag = fragment
    frag = re.sub(r"<br\s*/?>", "\n", frag, flags=re.I)
    frag = re.sub(r"</p\s*>", "\n", frag, flags=re.I)
    frag = re.sub(r"</li\s*>", "\n", frag, flags=re.I)
    frag = re.sub(r"<[^>]+>", "", frag)
    frag = _html.unescape(frag).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in frag.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def parse_announcement_detail(page_html: str, url: str) -> dict:
    """Parse one announcement page.

    Returns {"title", "date", "body", "links": [{"text","url"}],
    "url"}. The date comes from the meta description header
    "DUYURU (12 Kasım 2026)" when present; the body is the cleaned
    text of the col-sm-9 article column with the repeated title line
    dropped. Links are the distinct hrefs inside the article column
    (dokuman.osym.gov.tr PDFs first).
    """
    title_m = re.search(r"<title>(.*?)</title>", page_html, re.S)
    title = _clean(title_m.group(1)) if title_m else ""
    title = re.sub(
        r"\s*\|\s*T\.C\. Ölçme.*$", "", title
    )  # strip the site suffix
    col = _extract_col9(page_html)
    if not title:
        # Fallback: first heading inside the article column.
        hm = re.search(r"<h[123][^>]*>(.*?)</h[123]>", col, re.S)
        if hm:
            title = _clean(_html_to_text(hm.group(1)))

    date = None
    desc_m = re.search(
        r'<meta name="description" content="([^"]*)">', page_html, re.S
    )
    if desc_m:
        dm = re.search(r"\((\d{1,2}\s+\S+\s+\d{4})\)", _html.unescape(desc_m.group(1)))
        if dm:
            date = dm.group(1)

    col = _extract_col9(page_html)
    links: list[dict] = []
    seen: set[str] = set()
    for href, inner in re.findall(
        r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', col, re.S
    ):
        href = _clean(href)
        if not href or href in seen or href.startswith("#"):
            continue
        seen.add(href)
        if href.startswith("/"):
            href = BASE + href
        links.append({"text": _clean(_html_to_text(inner)) or href, "url": href})
    # dokuman.osym.gov.tr PDFs first — they are the guides/attachments
    links.sort(key=lambda l: (0 if "dokuman.osym.gov.tr" in l["url"] else 1, l["url"]))

    body = _html_to_text(col)
    # Drop the repeated title line (first line == title) if present.
    blines = body.split("\n")
    if blines and normalize_tr(blines[0]) == normalize_tr(title):
        blines = blines[1:]
    # Drop the breadcrumb-ish "Ana Sayfa / ..." line if it leaked in.
    blines = [ln for ln in blines if ln != "Ana Sayfa"]
    return {
        "title": title,
        "date": date,
        "body": "\n".join(blines).strip(),
        "links": links,
        "url": url,
    }


# ---------------------------------------------------------------------------
# Exam calendar (/Sayfa/SinavTakvimi)
# ---------------------------------------------------------------------------

_CAL_COLUMNS = [
    "exam_name",
    "pre_application_dates",
    "application_dates",
    "late_application_dates",
    "exam_date",
    "pre_application_result_date",
    "result_date",
    "preference_dates",
]


def parse_calendar(page_html: str) -> list[dict]:
    """Parse the calendar <table> into one dict per exam row.

    The first cell holds the short code + full name on separate lines
    ("e-YDS\nElektronik Yabancı Dil Sınavı\ne-YDS 2026/1 İngilizce");
    exam_name keeps the whole cleaned cell, exam_short the first line.
    "-" cells become None. Date ranges that run together in the source
    ("07.01.2026 14:0015.01.2026 23:59") are kept verbatim.
    """
    m = re.search(r"<table[^>]*>(.*?)</table>", page_html, re.S)
    if not m:
        return []
    rows: list[dict] = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)
        if not cells:
            continue
        cleaned = [_html_to_text(c) for c in cells]
        if cleaned and normalize_tr(cleaned[0]).startswith("sınav adı"):
            continue  # header row
        if len(cleaned) < 2:
            continue
        # First cell: short code on line 1, full name on the following
        # lines — keep both (cleaned text keeps the line breaks).
        name_lines = [ln for ln in cleaned[0].split("\n") if ln.strip()]
        row = {"exam_short": name_lines[0].strip() if name_lines else ""}
        for i, col in enumerate(_CAL_COLUMNS):
            val = cleaned[i] if i < len(cleaned) else ""
            val = _clean(val)
            row[col] = None if val in ("", "-") else val
        rows.append(row)
    return rows


def filter_calendar(rows: list[dict], query: str | None = None,
                    upcoming_only: bool = False) -> list[dict]:
    """Turkish-insensitive filter on exam name/short code. upcoming_only
    keeps rows whose exam_date contains a date in the future — the
    calendar is for the current year, so 'upcoming' means the exam
    date's last DD.MM.YYYY is today or later (best effort; rows with
    no parseable exam date are dropped)."""
    from datetime import date as _date

    q = normalize_tr(query) if query else None
    today = _date.today()
    out = []
    for r in rows:
        if q:
            hay = normalize_tr(f"{r.get('exam_short','')} {r.get('exam_name','')}")
            if q not in hay:
                continue
        if upcoming_only:
            exam_date = r.get("exam_date") or ""
            found = re.findall(r"(\d{2})\.(\d{2})\.(\d{4})", exam_date)
            if not found:
                continue
            last = max(
                _date(int(y), int(mo), int(d)) for d, mo, y in found
            )
            if last < today:
                continue
        out.append(r)
    return out


# ---------------------------------------------------------------------------
# Exam groups
# ---------------------------------------------------------------------------

def parse_group_title(page_html: str) -> str | None:
    """Group name from the page <title> ("e-TEP : Elektronik ... | ...")."""
    m = re.search(r"<title>(.*?)</title>", page_html, re.S)
    if not m:
        return None
    title = _clean(m.group(1))
    return re.sub(r"\s*\|\s*T\.C\. Ölçme.*$", "", title) or None


def resolve_group(group: str) -> tuple[int, str]:
    """Resolve a group code ("yks"), full name ("Kamu Personel Seçme
    Sınavı") or numeric id ("3") to (id, short code). Raises ValueError
    on unknown input."""
    g = (group or "").strip()
    if g.isdigit():
        gid = int(g)
        for code, (i, _full) in EXAM_GROUPS.items():
            if i == gid:
                return gid, code
        raise ValueError(
            f"unknown exam group id {gid!r}; use osym_exam_group() "
            "with no argument to list all groups"
        )
    key = normalize_tr(g)
    if key in EXAM_GROUPS:
        return EXAM_GROUPS[key][0], key
    # match by full name
    for code, (i, full) in EXAM_GROUPS.items():
        if normalize_tr(full) == key:
            return i, code
    raise ValueError(
        f"unknown exam group {group!r}; use osym_exam_group() "
        "with no argument to list all groups"
    )


def list_groups() -> list[dict]:
    """All exam groups, deduplicated by id, sorted by id."""
    seen: dict[int, dict] = {}
    for code, (gid, full) in EXAM_GROUPS.items():
        seen.setdefault(gid, {"id": gid, "code": code, "name": full})
    return [seen[k] for k in sorted(seen)]
