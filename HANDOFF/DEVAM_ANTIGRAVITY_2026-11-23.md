# Devam talimatı — "test edilmemiş her şey" turu (2026-11-23)

Önce oku: `CLAUDE.md` (proje kuralları, bağlayıcı), Obsidian `Borsa Durum/Borsa - Genel Durum ve Nerede Kaldik 2026-11-22.md`,
`Borsa - Order Flow Araclari Istisare ve Is Bolumu 2026-11-22.md`, `Is Sonuclari.md` son kayıt.

## Durum
- Son sonuç commit'i: ea7f59d (3./4. futures turu, 8/8 GEÇMEDİ; limit vs market ölçümü).
- Databento: yeni anahtar `strategy-lab/.env` içinde (`DATABENTO_API_KEY`), auth çalışıyor. **Anahtarı asla yazdırma/commit etme.**
  Kredi ~$125 (yarım kalan x1h indirmesi birkaç $ yemiş olabilir; portaldan bakılmadı).
- Ham CME verisi `strategy-lab/outputs/databento/` altında, git dışı (lisans). Commit etme.
- Python: `%USERPROFILE%\vectorbt-lab\.venv\Scripts\python.exe` (databento paketi orada). strategy-lab klasöründen koş.

## Sıradaki adımlar (sırayla, atlama)
1. `HANDOFF/istisare_2026-11-22_kural_tanimlari.json` (Argon'un kural tanımları) denetle: kaynaksız sayıları işaretle,
   look-ahead / bar içi sıra / kuyruk iyimserliği riskleri.
2. **Ön-kayıt yaz ve commit et (VERİYE BAKMADAN).** `HANDOFF/futures_tur5_onkayit_2026-11-23.md`. Hipotezler:
   - OF1 emilim, OF2 stacked imbalance, OF3 delta sapması — NQ trades (agresör taraflı), 2026-03-01 – 11-19, RTH.
   - OF4 iceberg — NQ mbo 10 gün (2026-10-05..16): yalnız BETİMLEYİCİ (n yetersiz), karar kuralı yok.
   - O1 opex — ES/NQ 1m mevcut veri (2010–2026).
   - X1 IBS CL/ZN/6E — günlük v.0 (mevcut `vdaily`); X2 Donchian N20 1h CL/ZN/6E (x1h).
   - Bonferroni tüm aile sayısıyla. Geçme: merkez maliyette CI alt sınırı > 0 + iki yarı > 0 + 2× > 0
     (önceki turlarla aynı; değiştirilecekse ön-kayıtta, sonuç görmeden).
   - Maliyet: ölçülmüş (MNQ 0.555, MES 0.247 puan/yön; CL/ZN/6E için bbo-1m'den ölçülecek). 3 satır rapor.
   - Thin-day kuralı: RTH işlem sayısı medyanın %50'sinden az olan gün atlanır (roll haftası).
3. İndir (önce `get_cost`, sonra): `python ../HANDOFF/scripts_2026-11-21/fetch_extra.py <paket>`
   paketler: `x1h` (~$2.9), `bbox` (~$4.4), `nqtrades2` (~$63.5), `nqmbo` (~$20.9). Toplam ~$92.
   Not: mevcut nqtrades `NQ.c.0` (2026-09..11), yeni nqtrades2 `NQ.v.0` (2026-03..09).
4. Betikleri yaz (`HANDOFF/scripts_2026-11-23/`), koş, sonuçları ön-kayda SONUÇ bölümü olarak ekle.
5. Elenenleri `strategy-lab/intraday/elenenler.py` kataloğuna ekle (kapsamda canlı modülleri dışarıda bırak),
   `python -m pytest intraday/test_elenenler.py -q`.
6. Commit + `git pull --rebase` + push. Obsidian: yeni not + Borsa MOC linki + `Is Sonuclari.md` 5 satır.

## Kurallar (kısa)
- Yön önerme, sayı uydurma, kötü sonucu saklama. Sonuca bakıp kural değiştirmek yasak (post-hoc).
- Geçen çıkarsa bile LIVE'a girmez; sonraki adım forward PAPER.
