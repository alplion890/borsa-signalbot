# Borsa Signal Bot

Maven 5K BNPL challenge icin ucretsiz piyasa verisi, MT5 forward defteri ve
Telegram bildirimleri kullanan manuel islem yardimcisidir. Otomatik emir acmaz;
brokerdaki son karar ve emir kullanicidadir.

## Guncel duzen (2026-09-12)

- **Mekanik ray dondurulmus:** tek gercek-para yetkili modul
  `SWEEP_CORE_AVOID_MID_VWAP` (NASDAQ100/US100, 15dk). NQ_ORB 2026-09-11'de
  negatif forward sonucu nedeniyle tarama ve Telegram listesinden cikarildi.
- **Diskresyoner ray birincil:** kullanici guncel teknik/makro olgulari
  yorumlar, tez ve curuteni onceden kaydeder; emir MT5/Maven'da elle girilir.
- **Arastirma rayi uykuda:** yeni strateji/parametre canliya eklenmez. Adaylar
  ayri PAPER defterinde ve sifir portfoy agirligiyla olculur.
- `default_modules()` tarama listesinde SWEEP_CORE ile PAPER EUR/GBP London
  modulleri vardir; LIVE/PAPER yetkisinin tek kaynagi `signalbot/risk.py`dir.
- Hafta ici 16:20 ve 18:15 TR hedeflerinde iki kisa Telegram mesaji uretilir.
  GitHub Actions cron yogunlugunda gecikebilir.
- Telegram NQ hacmi, onceki 20 ardil bar yerine onceki 20 islem gununun ayni
  New York 15dk saat dilimi medyanina gore normalize edilir. Bu yalniz piyasa
  baglamidir; SWEEP_CORE sinyal filtresi degildir.
- Challenge riski normal `%1.5`, onceki kapanan islem kazandiysa `%3`;
  PAPER moduller gercek para riski tasimaz.

Telefon kullanim kurallari: [TELEFON/SISTEM.md](TELEFON/SISTEM.md).
Signalbot kurulumu ve GitHub Actions ayrintilari:
[signalbot README](strategy-lab/intraday/signalbot/README.md).
