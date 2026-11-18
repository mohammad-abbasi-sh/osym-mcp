# osym-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/osym-mcp

Unofficial **read-only** MCP server for **ÖSYM** (www.osym.gov.tr) — Türkiye's national exam authority (T.C. Ölçme, Seçme ve Yerleştirme Merkezi): the **announcements index** (476 announcements in 2026 as of 18 Nov 2026, searchable per year back to 2010), **full announcement texts** with their guide PDFs, the **official exam calendar** (95 exams: YKS, KPSS, ALES, TUS, YDS, DGS, e-YDS, e-TEP and ~30 more groups, with application / late-application / exam / result / preference dates), and **per-group announcement lists**.

> Part of the "Turkey MCP factory". Not affiliated with ÖSYM. Data comes from ÖSYM's own public pages (server-rendered HTML) — no login, no API key, read-only. Personal exam results live behind a login at sonuc.osym.gov.tr / ais.osym.gov.tr and are **not** covered: this server only exposes the public announcements, calendar and group pages.

## For AI agents

- **Announcements**: `osym_latest_announcements` returns the newest items first (title, date DD.MM.YYYY, slug, URL). The index page serves one year at a time — pass `year` (2010–2026) for older years (`/Duyurular/Index/2025` returns 2025's 507 items).
- **Search is Turkish-insensitive**: `"kpss"` finds `"KPSS"`, `"sonuc"` finds `"Sonuçları"`. Search runs over the full year's list (476 items in 2026).
- **Full text**: `osym_get_announcement` takes a slug (or a full osym.gov.tr URL) and returns the title, date, body text and links — guide PDFs on dokuman.osym.gov.tr come first.
- **Calendar**: `osym_exam_calendar` returns one row per exam with 8 date columns. `"-"` cells (not applicable) are `null`; date ranges that run together on the site (`"07.01.2026 14:0015.01.2026 23:59"`) are kept verbatim. `query` filters by exam name/code (`"yks"`, `"kpss"`, `"e-yds"`); `upcoming_only` keeps exams whose exam date is today or later.
- **Groups**: `osym_exam_group` with no argument lists all 30+ exam groups (code, id, full name); with a code (`"yks"`), full name (`"Kamu Personel Seçme Sınavı"`) or numeric id (`"3"`) it returns that group's announcements.
- Every response carries `fetched_at` (UTC) and `source: www.osym.gov.tr`.

## Install

```bash
uvx osym-mcp
```

Or add to your MCP client config (e.g. Claude Desktop):

```json
{
  "mcpServers": {
    "osym": {
      "command": "uvx",
      "args": ["osym-mcp"]
    }
  }
}
```

## Tools

| Tool | What it does |
| --- | --- |
| `osym_latest_announcements` | Newest ÖSYM announcements, newest first (limit 1–50; optional `year` 2010–2026) |
| `osym_search_announcements` | Search announcements by title, Turkish-insensitive (optional `year`, limit 1–50) |
| `osym_get_announcement` | Full text of one announcement by slug or URL, with guide-PDF links |
| `osym_exam_calendar` | Official exam calendar: 95 exams with application / exam / result / preference dates (optional `query`, `upcoming_only`) |
| `osym_exam_group` | One exam group's announcements — or the full group list when called with no argument |
| `osym_health` | Is ÖSYM's site reachable right now? |

## Example

Latest announcements, 18 November 2026:

```json
{ "year": "current", "count": 2, "total_on_page": 476,
  "announcements": [
    { "title": "2026-GUY/2 Sınava Giriş Belgeleri Erişime Açıldı",
      "date": "16.11.2026",
      "slug": "2026-guy2-sinava-giris-belgeleri-erisime-acildi",
      "url": "https://www.osym.gov.tr/2026-guy2-sinava-giris-belgeleri-erisime-acildi" },
    { "title": "2026 KPSS Ön Lisans Sınavı: Branş Bazında Sıralamalar",
      "date": "12.11.2026",
      "slug": "2026-kpss-on-lisans-sinavi-brans-bazinda-siralamalar",
      "url": "https://www.osym.gov.tr/2026-kpss-on-lisans-sinavi-brans-bazinda-siralamalar" } ] }
```

## Caveats

- Verify dates on www.osym.gov.tr before acting on them — the calendar is the current year's and ÖSYM updates it through the year.
- The announcements index serves one year per request; searching another year needs the `year` argument.
- Announcement bodies are Word-pasted HTML on the site; the tools return cleaned plain text.
- Personal results (scores, rankings, placements) need a candidate login and are not covered.
- Transport uses Chrome TLS impersonation with a plain-requests fallback; requests are spaced ~0.5s apart.

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_parse.py -v   # offline, recorded fixtures
.venv/bin/python -m pytest tests/test_live.py -v    # live, against www.osym.gov.tr
.venv/bin/python tests/smoke_live.py                # daily CI probe
```

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — free for personal and non-commercial use; commercial use needs a separate license.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
