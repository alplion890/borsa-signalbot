# Signalbot — güncel durum (2026-09-30)

Karar kaynağı: [güncel tablo](../TELEFON/GUNCEL_EDGE_KARARLARI.md).

- Aktif mekanik tarama: yalnız NQ Sweep; LIVE yetkisi manuel karar/emir anlamındadır.
- EMA12: ayrı Yahoo NQ=F PAPER gözlem; gerçek zamanda ilk kayıt/teslim henüz doğrulanmadı.
- EUR/GBP London, NQ ORB ve Gold ORB emekli. EUR/GBP yeni forward girişi üretmez.
- 9 eski CAND_ deneyi arka planda sessiz ölçülür; Telegram fırsatı veya LIVE yetki değildir.
- Windows görevleri: NQ-Mobile 16:00–20:00 TR/5dk, Telegram-Defter her dakika, kapsam alarmı 20:10. London görevi kaldırıldı.
- Haber: yerel Investing/ECB/BoE RSS ve resmî takvim; ayrı GitHub Finnhub. GitHub schedule gecikebilir; PC kapalıyken kesintisiz kapsama güvencesi yok.
- Günlük fon/brifing tekrarı kapalı. MT5 yalnız salt okunur bağlam; emir kullanıcıda.
- 30 Eylül tam yerel test: 556 passed, 3 skipped. GitHub kuru koşu 36772166782 başarılı; gerçek aday/PNG teslimini doğrulamaz.
- Açık operasyon eksikleri: 30 Eylül mobil kapsam 3/21; NQ-Mobile son Windows hata kodu 1'in nedeni ayrıca incelenmeli. Bu belge strateji emekliliğini tamamlar; kapsam sorununu çözülmüş göstermez.

Gerekçe: [EUR/GBP emekliliği](../HANDOFF/eur_gbp_emeklilik_2026-09-30.md).
Eski teknik durum kopyası silindi; [emeklilik gerekçesi](../HANDOFF/eur_gbp_emeklilik_2026-09-30.md).

Ayrı ForwardEA-5dk görevi de kayıtlıdır: MT5 açılınca son işlenmiş mumdan sonraki broker barlarını sanal deftere işler. Üç Borsa-* + ayrı ForwardEA görevi vardır. Emir vermez; kapanmış veya backfill gözlemleri güncel Telegram fırsatı yapmaz. Ayrıntı: HANDOFF/mt5_telafi_temizligi_2026-09-30.md.
