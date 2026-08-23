# HANDOFF — Claude → Hermes

## Durum (2026-08-24)

Diskresyoner defter denetimin geçti, iki eklemen (aday kaydı + etiket
kolonları) yapıldı, ayrıca katman kapısı (≥3/4) koda gömüldü. Telegram
düzeltildi (yanlış bot tespit edilip doğrusuna geçildi). Detay git
geçmişinde: `git log --oneline -- HANDOFF/`, ilgili commit `44cf436`.

## Açık soru (cevap bekliyor)

**Hipotez-ailesi şablonuna ekleme öneriyorum:** *"havuz = bağımsız olay
sayısı; örtüşen bacaklar ortalanır."* `macro_day_drift_nq` tam bu yüzden
elendi (464 satır aslında 116 olaydı). Şablona yazılmazsa aynı hata
çok-enstrümanlı aile-kayıtlarında tekrar eder. Şablon senin, sen yaz —
sadece maddeyi unutma.

## Bugünkü ek: seans brifingi scripti

`intraday/forward_ea/seans_brief.py` — diskresyoner seans için olgu-only
brifing (takvim, fiyat, 200EMA uzaklığı, ATR/hacim yüzdeliği, dönüş
seviyeleri). Kullanıcı "sen yorum yapma, olayları söyle, ben yorumlarım"
dedi; script bu ayrımı korumak için var — hiçbir alan "güçlü/zayıf" gibi
yorum sıfatı kullanmıyor, sadece sayı/yüzdelik/tarih.
