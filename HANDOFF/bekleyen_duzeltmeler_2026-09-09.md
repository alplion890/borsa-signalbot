# Bekleyen düzeltmeler — 2026-09-09
# Claude Sonnet 4.6 tespiti. GPT denetiminden geçti, elle yapılacak kaldı.

---

## 1. forward_ledger.csv — exit_time < entry_time (3 satır, VERİ bozulması)

**Dosya**: `strategy-lab/outputs/intraday/forward_ea/forward_ledger.csv`

Üç satırda exit_time, entry_time'dan ÖNCE. Fiziksel olarak imkânsız.

```
Satır 157: CAND_NQ_DUAL_THRUST  entry=2026-09-01 14:45  exit=2026-09-01 11:45
Satır 161: NQ_ORB_STRONG_TREND  entry=2026-09-01 16:30  exit=2026-09-01 10:15
Satır 171: NQ_ORB_STRONG_TREND  entry=2026-09-07 14:55  exit=2026-09-04 20:45
```

**Neden ellenilmedi**: Doğru exit_time değerleri bilinmiyor; uydurma = backfill yanılgısı.
Satır 171 (3 gün sapma) büyük olasılıkla hayalet pozisyon — state JSON kaybından sonra
yeniden yazılmış. Satır 161, NQ_ORB'un forward n=25 sayımında yer alıyor ve
+1.35R ekliyor; gerçek değilse exp_R daha negatif.

**Yapılacak** (kullanıcı kararı gerekir):
- MT5 geçmiş işlemlerinden ya da forward_state.json.bak dosyasından doğru
  exit_time'ı bul. Bulunamazsa satırı `backfill=1` olarak işaretle veya sil.
- Sonra aşağıdaki kod düzeltmesini ekle.

**Engellenen kod düzeltmesi** (`ledger.py:_dogrula_degerler`):
Bu doğrulama şu an eklenemez çünkü CSV bozukken `oku_defter` ValueError atar
ve tüm sistem çöker (tripwire dahil). Veri temizlendikten sonra şu blok eklenebilir:

```python
# _dogrula_degerler() içine — mevcut kontrollerin sonuna:
if "exit_time" in df.columns:
    has_exit = df["exit_time"].notna()
    try:
        et = pd.to_datetime(df["entry_time"], errors="coerce")
        xt = pd.to_datetime(df["exit_time"], errors="coerce")
        _bildir(has_exit & (xt < et), "'exit_time' entry_time'dan once")
    except Exception:
        sorunlar.append("'exit_time' karsilastirilamadi")
```

---

## 2. cloud_runner._existing_keys — ham pd.read_csv (KOD, düşük önem)

**Dosya**: `strategy-lab/intraday/forward_ea/cloud_runner.py:76`

```python
old = pd.read_csv(ledger_path)  # oku_defter yerine ham okuma
```

Tek okuyucu ilkesinden sapıyor. Eksik kolonda `KeyError` verir (fail-closed kalır
ama hata mesajı kötü). Şema çakışmasını yakalamıyor.

**Neden ellenilmedi**: Cloud runner GitHub Actions'ta çalışıyor.
`oku_defter` kullanımına geçmek: cloud_ledger bozuksa Actions adımı hata atar ve
Telegram'a hata bildirimi gider — mevcut sessiz KeyError yerine gürültülü hata.
Davranış değişikliği; düşük önem, acil değil.

**Yapılacak** (isteğe bağlı bakım):
`_existing_keys` içinde `pd.read_csv` yerine:
```python
try:
    old = ledger.oku_defter(ledger_path, "cloud_existing_keys")
except ValueError:
    return set()  # bozuk ledger -> temiz başla, append duplicate kontrolü yetersiz
                  # ama en azından crash etmez
```

---

## 3. OrderExecutor._week_start_equity — bellekte, kalıcı değil (DORMANT)

**Dosya**: `strategy-lab/intraday/forward_ea/order_executor.py:121`

`_week_start_equity` instance dict'i. Süreç yeniden başlayınca sıfırlanır.
Haftalık stop `risk.py` profilinde var ama `_weekly_dd_halt()` hiçbir zaman
tetiklenemez.

**Neden ellenilmedi**: Maven EA kullanımını yasaklıyor (`server execution` =
kural ihlali). `live_runner --live` modu pratikte kapalı; otomatik emir yolu
dormant. Kod kusuru gerçek, üretim riski sıfır. Dormant kod dokunulmazken
bozulmaya tercih edilir.

**Eğer ileride gerekirse**: `exec_day.json` mekanizmasının haftaya genişletilmesi
(bkz. önceki handoff BUG-2 açıklaması).

---

## Sıralama

| # | Dosya | Önem | Engel | Karar |
|---|-------|------|-------|-------|
| 1 | forward_ledger.csv satır 157/161/171 | ORTA | Doğru değer bilinmiyor | Kullanıcı kararı |
| 2 | cloud_runner._existing_keys | DÜŞÜK | Davranış değişikliği | İsteğe bağlı bakım |
| 3 | order_executor._week_start_equity | DÜŞÜK | Dormant yol | Dokunma |
