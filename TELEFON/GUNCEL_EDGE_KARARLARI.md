# Güncel edge ve filtre kararları — 2026-11-05

Kalıcı karar kaynakları (Obsidian): **Borsa - Tek Kaynak ve Bulut Rolu Karari 2026-11-05** ve **Borsa - Guncel Edge ve Filtre Kararlari 2026-09-27**.

**Tek ölçüm kaynağı: Maven MT5.** Bulut (Yahoo) defteri 2026-11-05'te donduruldu; arşivdir.

| Edge | Durum | Ölçüm |
|---|---|---|
| NQ Sweep | LIVE; manuel emir | Maven forward. Düşürme taahhüdü: n≥25 ve exp_R<0 → PAPER; birleşik sayım (MT5 ∪ donmuş bulut). |
| NQ ilk 5dk EMA12 | PAPER | Maven forward EA, `CAND_EMA12_FIRST5M`, 2026-11-05'ten itibaren. Telegram alarmı yok. |
| 9 CAND_ deneyi | PAPER, sessiz | Maven forward; Telegram'a çıkmaz. |
| EUR London | EMEKLİ — 2026-09-30 | Forward n=14, +3,812R; uzun tarih −0,097R. Yeniden yargılama adayı. |
| GBP London | EMEKLİ — 2026-09-30 | Arşiv testinde geleceğe bakış hatası bulundu (2026-10-29); sonuç geçersiz. |
| NQ ORB | EMEKLİ | Uzun tarih n=1907, +0,0276R. Yeniden yargılama adayı. |
| Gold NY ORB | EMEKLİ | Uzun tarih −0,0687R. |
| Donchian XAU 1H | Seçilmedi | Uzun tarih +0,083R (3× maliyette pozitif). Yeniden yargılama adayı. |

Yetki: `signalbot/risk.py`. Tarama: `forward_ea/modules.py:default_modules()`. Olumlu backtest yetkiyi değiştirmez. Otomatik emir açılmaz.

**Bulut botu:** Sweep alarmı (Yahoo verisi; girmeden önce Maven grafiğinde doğrula) + makro ölçüm (beklenti/gerçekleşen/sürpriz, NQ/XAU +15/+60 dk, ZT=F ve 5Y getiri bp) + haber başlığı. Yön bilgisi vermez.

**Diskresyoner ray:** 2026-11-05'te kaldırıldı (2026-09-03'ten beri 0 kayıt). Arşiv: `docs/archive/diskresyoner-2026-11-05/`.

Elenen edge'lerin adil değerlendirilmesi: [[Borsa - Strateji Eleme Adaleti ve Motor Denetimi 2026-10-29]].
