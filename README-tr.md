# osym-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/osym-mcp

**ÖSYM** (www.osym.gov.tr) için resmi olmayan, **salt okunur** MCP sunucusu — Türkiye'nin ulusal sınav kurumu (T.C. Ölçme, Seçme ve Yerleştirme Merkezi): **duyuru listesi** (18 Kasım 2026 itibarıyla 2026'da 476 duyuru, 2010'a kadar yıllara göre aranabilir), **duyuruların tam metinleri** ve kılavuz PDF'leri, **resmî sınav takvimi** (95 sınav: YKS, KPSS, ALES, TUS, YDS, DGS, e-YDS, e-TEP ve ~30 grup daha; başvuru / geç başvuru / sınav / sonuç / tercih tarihleriyle) ve **grup bazında duyuru listeleri**.

> "Turkey MCP factory" projesinin bir parçasıdır. ÖSYM ile bağlantısı yoktur. Veriler ÖSYM'nin herkese açık sayfalarından (sunucu tarafında oluşturulan HTML) alınır — giriş yok, API anahtarı yok, salt okunur. Kişisel sınav sonuçları sonuc.osym.gov.tr / ais.osym.gov.tr adreslerinde giriş gerektirir ve **kapsanmaz**: bu sunucu yalnızca herkese açık duyuruları, takvimi ve grup sayfalarını sunar.

## Yapay zekâ ajanları için

- **Duyurular**: `osym_latest_announcements` en yeni duyuruları önce döndürür (başlık, tarih GG.AA.YYYY, slug, URL). Liste sayfası bir seferde bir yıl sunar — eski yıllar için `year` (2010–2026) verin (`/Duyurular/Index/2025`, 2025'in 507 duyurusunu döndürür).
- **Arama Türkçe duyarsızdır**: `"kpss"`, `"KPSS"`yi bulur; `"sonuc"`, `"Sonuçları"`nı bulur. Arama, yılın tüm listesi üzerinde çalışır (2026'da 476 duyuru).
- **Tam metin**: `osym_get_announcement` bir slug (veya tam osym.gov.tr URL'si) alır; başlık, tarih, gövde metni ve bağlantıları döndürür — dokuman.osym.gov.tr üzerindeki kılavuz PDF'leri önce gelir.
- **Takvim**: `osym_exam_calendar` sınav başına bir satır ve 8 tarih sütunu döndürür. `"-"` hücreleri (geçerli değil) `null` olur; sitede bitişik yazılan tarih aralıkları (`"07.01.2026 14:0015.01.2026 23:59"`) aynen korunur. `query` sınav adı/koduna göre filtreler (`"yks"`, `"kpss"`, `"e-yds"`); `upcoming_only` yalnızca sınav tarihi bugün veya ileride olanları tutar.
- **Gruplar**: `osym_exam_group` argümansız çağrıldığında 30+ sınav grubunun tamamını listeler (kod, id, tam ad); kod (`"yks"`), tam ad (`"Kamu Personel Seçme Sınavı"`) veya sayısal id (`"3"`) ile o grubun duyurularını döndürür.
- Her yanıt `fetched_at` (UTC) ve `source: www.osym.gov.tr` taşır.

## Kurulum

```bash
uvx osym-mcp
```

Veya MCP istemci yapılandırmanıza ekleyin (ör. Claude Desktop):

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

## Araçlar

| Araç | Ne yapar |
| --- | --- |
| `osym_latest_announcements` | En yeni ÖSYM duyuruları, yeniden eskiye (limit 1–50; isteğe bağlı `year` 2010–2026) |
| `osym_search_announcements` | Başlığa göre duyuru arama, Türkçe duyarsız (isteğe bağlı `year`, limit 1–50) |
| `osym_get_announcement` | Bir duyurunun tam metni (slug veya URL ile), kılavuz PDF bağlantılarıyla |
| `osym_exam_calendar` | Resmî sınav takvimi: başvuru / sınav / sonuç / tercih tarihleriyle 95 sınav (isteğe bağlı `query`, `upcoming_only`) |
| `osym_exam_group` | Bir sınav grubunun duyuruları — argümansız çağrılırsa tüm grup listesi |
| `osym_health` | ÖSYM sitesine şu an erişilebiliyor mu? |

## Örnek

En yeni duyurular, 18 Kasım 2026:

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

## Dikkat edilecekler

- Tarihler konusunda işlem yapmadan önce www.osym.gov.tr adresinden doğrulayın — takvim güncel yıla aittir ve ÖSYM yıl içinde günceller.
- Duyuru listesi istek başına bir yıl sunar; başka bir yılı aramak için `year` argümanı gerekir.
- Duyuru gövdeleri sitede Word'den yapıştırılmış HTML'dir; araçlar temizlenmiş düz metin döndürür.
- Kişisel sonuçlar (puan, sıralama, yerleştirme) aday girişi gerektirir ve kapsanmaz.
- Aktarım, Chrome TLS taklidi ve düz requests yedeği kullanır; istekler ~0,5 sn arayla gönderilir.

## Geliştirme

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_parse.py -v   # çevrimdışı, kayıtlı örnekler
.venv/bin/python -m pytest tests/test_live.py -v    # canlı, www.osym.gov.tr karşısında
.venv/bin/python tests/smoke_live.py                # günlük CI denetimi
```

## Lisans

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — kişisel ve ticari olmayan kullanım için ücretsizdir; ticari kullanım ayrı bir lisans gerektirir.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
