# Güncel edge ve filtre kararları — 2026-09-27

Kalıcı karar kaynağı Obsidian **Borsa - Guncel Edge ve Filtre Kararlari 2026-09-27** notudur.

| Edge | Durum | Ek filtre |
|---|---|---|
| NQ Sweep | LIVE; manuel emir | Zorunlu makro/COT/OI/funding kapısı yok. |
| EUR London | EMEKLİ — 2026-09-30 | Seyrek sinyal ve zayıf uzun tarih kanıtı; güncel forward n=14, +3,812R. |
| GBP London | EMEKLİ — 2026-09-30 | Negatif uzun tarih ve forward; aktif tarama/ölçüm durdu. |
| NQ ORB | EMEKLİ | Tarama/Telegram dışında; filtreli sürüm araştırma adayı. |
| Gold NY ORB | EMEKLİ | Makro+COT araştırma adayı. |
| NQ ilk 5dk EMA12 | PAPER forward gözlem | Yahoo NQ=F; gerçek emir yok, LIVE yetkisi yok. |

Yetki: signalbot/risk.py. Tarama: forward_ea/modules.py:default_modules(). Olumlu backtest yetkiyi değiştirmez. Otomatik emir açılmaz.

İlk 5 dakika EMA12 fikri **kanıtlanmamış araştırma adayıdır**. 2026-09-29'da
ayrı PAPER forward gözlemine alındı; bu, mekanik modül listesine veya LIVE
riskine katılma değildir. Sinyal ve varsayımsal sonuçlar Telegram'da PAPER
etiketiyle görünür. Tek kaynak: Obsidian [[Borsa - Instagram Ilk 5dk EMA12 Testi 2026-09-29]].

Kanıt: [geniş makro/COT A/B raporu](../strategy-lab/outputs/intraday/cross_asset_positioning_ab/REPORT.md). Dar makro ve HTF/LTF deneyleri farklı karşılaştırmalardır, güncel seçilmiş sürüm değildir.

Diskresyoner: 2/4 + tez + çürüten + ön-kayıt. [Mobil akış](MOBIL_KARAR_AKISI.md). Telegram sessizliği fırsat yokluğu değildir; yerel 20:10 kapsam alarmı PC/oturum açıkken çalışır.

Eski modül listeleri/skorlar [tarihsel arşivdedir](../HANDOFF/archive/forward_ea_history_before_2026-09-27.md).

30 Eylül kararı: EUR/GBP aktif yerel/bulut taramasından ve yeni PAPER ölçümünden çıkarıldı. Eski defterler ve araştırma raporları korundu. Gerekçe: [[Borsa - EUR GBP London Emeklilik Karari 2026-09-30]].

Arka plandaki 9 CAND_ deneyi sessiz ölçümdür; aktif Telegram edge’i değildir. 30 Eylül kapsam boşluğu ve NQ-Mobile son hata kodu ayrıca çözülmelidir.
