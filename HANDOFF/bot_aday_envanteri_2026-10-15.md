# Bot aday envanteri — 2026-10-15

Mevcut MT5 PAPER ileri test kayıtları; backfill ve bulut toplamlarına eklenmedi. Eski satırlarda broker kimliği eksik; FTMO icra kanıtı değildir. Bu inceleme LIVE/PAPER yetkilerini değiştirmedi.

| Modül | n | Toplam R | Mevcut yetki |
|---|---:|---:|---|
| SWEEP_CORE_AVOID_MID_VWAP | 15 | +0.14 | Manuel LIVE yetkili |
| CAND_SWEEP_JAP225 | 13 | +3.79 | PAPER / araştırma |
| EUR_LONDON_FADE_EMA | 12 | +4.24 | Emekli |
| GBP_LONDON_STRONG_TREND | 19 | -5.56 | Emekli |
| CAND_NQ_DUAL_THRUST | — | veri karantinada | PAPER / araştırma |
| CAND_SP500_ORB | 32 | -0.66 | PAPER / araştırma |
| CAND_SWEEP_FRA40 | 6 | -4.49 | PAPER / araştırma |
| CAND_SWEEP_SP500 | 7 | +11.17 | PAPER / araştırma |
| CAND_SWEEP_UK100 | 7 | +6.82 | PAPER / araştırma |
| CAND_SWEEP_US2000 | 4 | -5.39 | PAPER / araştırma |
| CAND_SWEEP_US30 | 6 | -4.08 | PAPER / araştırma |
| GOLD_NY_ORB_TREND | 9 | -3.70 | Emekli |
| NQ_ORB_STRONG_TREND | — | veri karantinada | Emekli |
| SWEEP_ES_DIV | 4 | -0.56 | Emekli |

NQ Sweep manuel LIVE listesinde fakat n15 +0.14R ile güncel yerel toplam başa baş. Aynı broker geçmişinde Temmuz–14 Ekim mevcut backtest n13 -3.09R; bunun ileri testle bağımsız ek kanıt olduğu iddia edilmez.

JAP225 n13 +3.79R; SP500 Sweep n7 +11.17R; UK100 n7 +6.82R. Küçük örneklem ve sonuca göre seçim riski var; LIVE kanıtı değildir. NQ dahil bu dört sürüm FTMO demosunda ayrı sabit kayıtlarla teknik doğrulama/ölçüm adayları olarak sunuldu, devreye alınmadı.

EUR London yerel güncel sürüm n12 +4.24R, geçmiş birleşik n14 sayısıyla aynı kapsam değil. Emeklilik uzun tarih/sıklık gerekçeleriyle sürüyor. GBP/Gold/NQ ORB/Sweep ES DIV emekli.

Dual Thrust ve NQ ORB çıkış-zamanı hataları nedeniyle tüm modül kayıtları karantinada. EMA12 ayrı Yahoo PAPER gözlemi; bu oturumda yerel güncel sonuç dosyası bulunamadı, sayı uydurulmadı. BTC Binance adayında yerel normal forward satırı yok; MT5 kanıtı değil.

Araştırma raporları: NQ ORB 1s EMA filtreli sürüm yalnız yeni forward adayı; makro/COT/OI ve katman filtreleri LIVE onaylı değil. Gold makro Sweep ve intraday momentum raporları yeni işlem modülü seçmiyor. Faiz pilotu ayrı eksik araştırma.

İcra engeli: mevcut risk.py Maven profilleri ve sabit puan-değeri tablosu içeriyor; bunlar FTMO CFD lot/kontrat kuralları yerine kullanılamaz. FTMO sembol özellikleri ve hesaba özel risk profili doğrulanmadan otomatik emir devreye alınmaz.

Git pull yerel değişiklik/untracked çakışmasıyla durdu; zorla birleştirme yapılmadı. Kod/defter/emir değiştirilmedi.
