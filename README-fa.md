# osym-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/osym-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **ÖSYM** (سازمان ملی آزمون ترکیه، www.osym.gov.tr): **فهرست اطلاعیه‌ها** (تا ۱۸ نوامبر ۲۰۲۶، ۴۷۶ اطلاعیه در سال ۲۰۲۶؛ قابل جستجو بر اساس سال تا ۲۰۱۰)، **متن کامل اطلاعیه‌ها** همراه با فایل‌های PDF راهنما، **تقویم رسمی آزمون‌ها** (۹۵ آزمون: YKS، KPSS، ALES، TUS، YDS، DGS، e-YDS، e-TEP و حدود ۳۰ گروه دیگر؛ با تاریخ‌های ثبت‌نام، ثبت‌نام دیرهنگام، آزمون، اعلام نتیجه و انتخاب رشته) و **فهرست اطلاعیه‌های هر گروه آزمون**.

> بخشی از پروژهٔ «کارخانهٔ MCP ترکیه». وابسته به ÖSYM نیست. داده‌ها از صفحات عمومی خود ÖSYM (HTML سمت سرور) گرفته می‌شوند — بدون ورود، بدون کلید API، فقط‌خواندنی. نتایج شخصی آزمون در sonuc.osym.gov.tr و ais.osym.gov.tr نیازمند ورود هستند و **پوشش داده نمی‌شوند**: این سرور فقط اطلاعیه‌ها، تقویم و صفحات گروه‌های عمومی را ارائه می‌کند.

## برای ایجنت‌های هوش مصنوعی

- **اطلاعیه‌ها**: `osym_latest_announcements` جدیدترین اطلاعیه‌ها را اول برمی‌گرداند (عنوان، تاریخ به شکل DD.MM.YYYY، اسلاگ، URL). صفحهٔ فهرست در هر بار یک سال را ارائه می‌کند — برای سال‌های قبل `year` بدهید (۲۰۱۰ تا ۲۰۲۶)؛ مثلاً `/Duyurular/Index/2025` تعداد ۵۰۷ اطلاعیهٔ سال ۲۰۲۵ را برمی‌گرداند.
- **جستجو نسبت به ترکی حساس نیست**: `"kpss"` عبارت `"KPSS"` را پیدا می‌کند و `"sonuc"` عبارت `"Sonuçları"` را. جستجو روی کل فهرست سال انجام می‌شود (در ۲۰۲۶، ۴۷۶ اطلاعیه).
- **متن کامل**: `osym_get_announcement` یک اسلاگ (یا URL کامل osym.gov.tr) می‌گیرد و عنوان، تاریخ، متن بدنه و پیوندها را برمی‌گرداند — فایل‌های PDF راهنما در dokuman.osym.gov.tr اول می‌آیند.
- **تقویم**: `osym_exam_calendar` برای هر آزمون یک ردیف با ۸ ستون تاریخ برمی‌گرداند. سلول‌های `"-"` (نامربوط) به صورت `null` هستند؛ بازه‌های تاریخی که در سایت به‌هم‌چسبیده نوشته شده‌اند (`"07.01.2026 14:0015.01.2026 23:59"`) عیناً حفظ می‌شوند. `query` بر اساس نام/کد آزمون فیلتر می‌کند (`"yks"`، `"kpss"`، `"e-yds"`)؛ `upcoming_only` فقط آزمون‌هایی را نگه می‌دارد که تاریخ آزمونشان امروز یا آینده است.
- **گروه‌ها**: `osym_exam_group` بدون آرگومان، همهٔ ۳۰+ گروه آزمون را فهرست می‌کند (کد، شناسه، نام کامل)؛ با کد (`"yks"`)، نام کامل (`"Kamu Personel Seçme Sınavı"`) یا شناسهٔ عددی (`"3"`)، اطلاعیه‌های آن گروه را برمی‌گرداند.
- هر پاسخ شامل `fetched_at` (UTC) و `source: www.osym.gov.tr` است.

## نصب

```bash
uvx osym-mcp
```

یا به پیکربندی کلاینت MCP خود اضافه کنید (مثلاً Claude Desktop):

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

## ابزارها

| ابزار | کارکرد |
| --- | --- |
| `osym_latest_announcements` | جدیدترین اطلاعیه‌های ÖSYM، از جدید به قدیم (حد ۱ تا ۵۰؛ `year` اختیاری ۲۰۱۰ تا ۲۰۲۶) |
| `osym_search_announcements` | جستجوی اطلاعیه‌ها بر اساس عنوان، بدون حساسیت به ترکی (‏`year` اختیاری، حد ۱ تا ۵۰) |
| `osym_get_announcement` | متن کامل یک اطلاعیه با اسلاگ یا URL، همراه با پیوندهای PDF راهنما |
| `osym_exam_calendar` | تقویم رسمی آزمون: ۹۵ آزمون با تاریخ‌های ثبت‌نام، آزمون، نتیجه و انتخاب رشته (‏`query` و `upcoming_only` اختیاری) |
| `osym_exam_group` | اطلاعیه‌های یک گروه آزمون — بدون آرگومان، فهرست کامل گروه‌ها |
| `osym_health` | آیا سایت ÖSYM در حال حاضر در دسترس است؟ |

## مثال

جدیدترین اطلاعیه‌ها، ۱۸ نوامبر ۲۰۲۶:

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

## نکات

- پیش از هر اقدام بر اساس تاریخ‌ها، آن‌ها را در www.osym.gov.tr بررسی کنید — تقویم مربوط به سال جاری است و ÖSYM در طول سال آن را به‌روز می‌کند.
- فهرست اطلاعیه‌ها در هر درخواست یک سال را ارائه می‌کند؛ برای جستجوی سال دیگر باید آرگومان `year` را بدهید.
- بدنهٔ اطلاعیه‌ها در سایت به‌صورت HTML چسبانده‌شده از Word است؛ ابزارها متن سادهٔ پاک‌شده برمی‌گردانند.
- نتایج شخصی (نمره، رتبه، قبولی) نیازمند ورود داوطلب هستند و پوشش داده نمی‌شوند.
- انتقال داده با جعل TLS کروم و پشتیبان requests ساده انجام می‌شود؛ درخواست‌ها با فاصلهٔ حدود ۰٫۵ ثانیه فرستاده می‌شوند.

## توسعه

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_parse.py -v   # آفلاین، با نمونه‌های ضبط‌شده
.venv/bin/python -m pytest tests/test_live.py -v    # زنده، در برابر www.osym.gov.tr
.venv/bin/python tests/smoke_live.py                # بررسی روزانهٔ CI
```

## مجوز

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — برای استفادهٔ شخصی و غیرتجاری رایگان است؛ استفادهٔ تجاری نیازمند مجوز جداگانه است.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
