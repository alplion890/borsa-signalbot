# Signalbot — güncel durum (2026-10-01)

Karar kaynağı: [güncel tablo](../TELEFON/GUNCEL_EDGE_KARARLARI.md).

- Aktif mekanik tarama: yalnız NQ Sweep; LIVE yetkisi manuel karar/emir anlamındadır.
- EMA12: ayrı Yahoo NQ=F PAPER gözlem; gerçek zamanda ilk kayıt/teslim henüz doğrulanmadı.
- EUR/GBP London, NQ ORB ve Gold ORB emekli. EUR/GBP yeni forward girişi üretmez.
- 9 eski CAND_ deneyi arka planda sessiz ölçülür; Telegram fırsatı veya LIVE yetki değildir.
- Windows görevleri: NQ-Mobile hafta içi 09:00 TR–NYSE kapanışı/5dk (tatil/erken kapanış kapısı), Telegram-Defter her dakika, kapsam alarmı 20:10. London görevi kaldırıldı.
- Haber: yerel Investing/ECB/BoE RSS ve resmî takvim; ayrı GitHub Finnhub. GitHub gündüz işçisi kendi içinde her 5dk kontrol eder; 330dk sonunda yeni koşuya devreder. İlk başlangıç ve devirde GitHub kuyruğu gecikebilir.
- Günlük fon/brifing tekrarı kapalı. MT5 yalnız salt okunur bağlam; emir kullanıcıda.
- 30 Eylül tam yerel test: 556 passed, 3 skipped. GitHub kuru koşu 36772166782 başarılı; gerçek aday/PNG teslimini doğrulamaz.
- 1 Ekim inceleme: PC EMA12 penceresinde kapalıydı; GitHub cron o pencereye koşu başlatmadı. Yerel hata 1 ortak log dosyasındaki eşzamanlı yazma çakışmasından geldi; loglar ayrıldı, gerçek görev koşuları başarıyla doğrulandı. 567 passed, 3 skipped. Yeni kapsam: HANDOFF/gun_boyu_tarama_2026-10-01.md.

Gerekçe: [EUR/GBP emekliliği](../HANDOFF/eur_gbp_emeklilik_2026-09-30.md).
Eski teknik durum kopyası silindi; [emeklilik gerekçesi](../HANDOFF/eur_gbp_emeklilik_2026-09-30.md).

MT5 ölçüm telafisi: ayrıca kayıtlı ForwardEA-5dk görevi terminal açıkken her 5dk yalnız sanal defteri ilerletir. Terminal kapanınca state durur; açılınca erişilebilir eksik broker mumlarını sırayla işler. Emir vermez, eski/kapanmış fırsatı güncel Telegram çağrısı yapmaz. Üç Borsa-* görevi + ayrı ForwardEA görevi vardır. Ayrıntı: HANDOFF/mt5_telafi_temizligi_2026-09-30.md.
