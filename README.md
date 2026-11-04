# Borsa Signal Bot

Güncel modül ve filtre kararları: [tek karar tablosu](TELEFON/GUNCEL_EDGE_KARARLARI.md) (2026-09-27).

Maven 5K BNPL challenge icin ucretsiz piyasa verisi, MT5 forward defteri ve
Telegram bildirimleri kullanan manuel islem yardimcisidir. Otomatik emir acmaz;
brokerdaki son karar ve emir kullanicidadir.

## Guncel duzen (2026-09-16)

- **Mekanik ray dondurulmus:** tek gercek-para yetkili modul
  `SWEEP_CORE_AVOID_MID_VWAP` (NASDAQ100/US100, 15dk). NQ_ORB 2026-09-11'de
  negatif forward sonucu nedeniyle tarama ve Telegram listesinden cikarildi.
- **Diskresyoner ray birincil:** kullanici guncel teknik/makro olgulari
  yorumlar, tez ve curuteni onceden kaydeder; emir MT5/Maven'da elle girilir.
- **Arastirma rayi sinirli ve aktif:** yeni veri once temizlenir; ilk ve tek
  on-kayitli calisma, mevcut SWEEP_CORE'un NQ-ES goreceli guc filtresiyle
  kaynak-dayanikliligini PAPER'da sinamaktir. Sonuc LIVE kuralini veya riski
  otomatik degistirmez. Sifirdan edge aramasi bu calismanin ardindan gelir.
- **Diskresyoner rayda haber + teknik birlikte olculur:** olay oncesi beklenti,
  gerceklesen/revizyon, ilk piyasa tepkisi, tez ve curuten makro defterine
  yazilir. Giris kapisi en az 2/4'tur: narrative, hacim, trend,
  destek/seviye. Kalan katmanlar ayni anda guclu ters bilgi vermiyorsa celiski
  sayilmaz; guclu celiskide ya daha guclu kanit gerekir ya da islem alinmaz.
- `default_modules()` tarama listesinde yalnız SWEEP_CORE
  modulu vardir; LIVE/PAPER yetkisinin tek kaynagi `signalbot/risk.py`dir.
- Gunluk otomatik fon/brifing mesaji 2026-09-28'de durduruldu; yerel gercek tarayici ve olay bildirimleri icin [mobil akis](TELEFON/MOBIL_KARAR_AKISI.md).
  GitHub Actions cron yogunlugunda gecikebilir.
- Telegram NQ hacmi, onceki 20 ardil bar yerine onceki 20 islem gununun ayni
  New York 15dk saat dilimi medyanina gore normalize edilir. Bu yalniz piyasa
  baglamidir; SWEEP_CORE sinyal filtresi degildir.
- Challenge riski normal `%1.5`, onceki kapanan islem kazandiysa `%3`;
  PAPER moduller gercek para riski tasimaz.

Telefon kullanim kurallari: [TELEFON/SISTEM.md](TELEFON/SISTEM.md).
ChatGPT/Claude/Gemini proje dosyasi:
[TELEFON/MAVEN_AI_MASTER.md](TELEFON/MAVEN_AI_MASTER.md).
Signalbot kurulumu ve GitHub Actions ayrintilari:
[signalbot README](strategy-lab/intraday/signalbot/README.md).


2026-09-30 güncel karar: EUR_LONDON_FADE_EMA ve GBP_LONDON_STRONG_TREND emekli; yeni yerel/bulut tarama ve forward kaydı yok. Sweep LIVE manuel, EMA12 ayrı PAPER gözlem. NQ ORB/Gold emekli; filtreli makro/COT sürümleri araştırmadır. Gerekçe: HANDOFF/eur_gbp_emeklilik_2026-09-30.md.
