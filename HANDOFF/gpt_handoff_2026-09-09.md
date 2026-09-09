# GPT Handoff — borsa projesi kod incelemesi
# Tarih: 2026-09-09 | Claude Sonnet 4.6 tarafından üretildi

---

## Proje özeti

Maven $5K BNPL challenge için diskresyoner + mekanik forward test sistemi.
Python, Windows, MT5 bağlantısı, GitHub Actions bulut ölçümü.

Dizin: `borsa/strategy-lab/`

```
intraday/
  forward_ea/          # Ana motor: engine, ledger, cloud_runner, live_runner, diskresyoner
  signalbot/           # risk.py, telegram bildirimi, Telegram signal scanner
  mt5_bridge/          # mt5_io.py, reality_profiler
.github/workflows/     # cloud_ledger.yml (saatlik GitHub Actions)
```

---

## 3 raylı düzen

| Ray | Durum | Tek canlı modül |
|-----|-------|-----------------|
| Mekanik | DONDURULMUŞ | `SWEEP_CORE_AVOID_MID_VWAP` (LIVE, gerçek emir) |
| Diskresyoner | BİRİNCİL | Elle yorum, `diskresyoner.py` defteri |
| Araştırma | UYKUDA | — |

---

## Bulgular — incelenen dosyalar

1. `forward_ea/engine.py` — feed-agnostik çekirdek döngü
2. `forward_ea/order_executor.py` — gerçek MT5 emir katmanı
3. `forward_ea/ledger.py` — tek kanıt kapısı (`oku_defter`)
4. `forward_ea/cloud_runner.py` — GitHub Actions ölçüm kopyası
5. `forward_ea/live_runner.py` — yerel MT5 döngüsü
6. `forward_ea/diskresyoner.py` — diskresyoner defter
7. `forward_ea/modules.py` — canlı + aday modüller
8. `forward_ea/positions.py` — PaperPosition, Book
9. `signalbot/risk.py` — TEK risk kaynağı (LIVE/PAPER tier, profiller)
10. `mt5_bridge/mt5_io.py` — MT5 bağlantı adaptörü
11. `mt5_bridge/reality_profiler.py` — spread/slippage gerçek maliyet profili
12. `forward_ea/cloud_feed.py` — bulut veri yönlendirme
13. `.github/workflows/cloud_ledger.yml` — saatlik Actions workflow
14. `signalbot/test_demotion_tripwire.py` — LIVE→PAPER demotion tetikleyici
15. `forward_ea/test_live_whitelist.py` — LIVE modül liste bütünlüğü testi

---

## HATALAR

### BUG-1 — KRİTİK: NQ_ORB_STRONG_TREND hâlâ `default_modules()` içinde

**Dosya**: `forward_ea/modules.py:245`

```python
# BU SATIR HÂLÂ MEVCUT — kaldırılmamış
LiveModule("NQ_ORB_STRONG_TREND", "NASDAQ100", "5m", 1.0, 48,
           _orb_detector(nq_orb, adx_min=28.0)),
```

**Kanıt**: CLAUDE.md (proje talimatı) açıkça diyor:
> "NQ_ORB 2026-09-04'te düşürme taahhüdü tetiklendi, n=25 exp_R=−0.106 → PAPER'a düştü"

`risk.py` yorumu da teyit ediyor:
> "NQ_ORB_STRONG_TREND 2026-09-04'te dusuruldu"

`test_live_whitelist.py` yorumu:
> "NQ_ORB_STRONG_TREND 2026-09-04'te dusuruldu (forward n=25, exp_R=-0.106)"

**Etki**: Modül hâlâ Telegram'a sinyal atıyor ("telefona sinyal düşüyor"). GOLD için yapılan emekliye alma (2026-08-28) burada uygulanmadı. GOLD için test var (`test_GOLD_artik_default_modules_de_DEGIL`), NQ_ORB için yok.

**Yapılacak**:
1. `modules.py:245-246` satırlarını sil (NQ_ORB LiveModule tanımı)
2. `modules.py:230` docstring'i güncelle ("GUNCEL (2026-08-28)" → "(2026-09-09)")
3. `test_live_whitelist.py`'e yeni test ekle:

```python
def test_NQ_ORB_artik_default_modules_de_DEGIL() -> None:
    """NQ_ORB_STRONG_TREND 2026-09-04'te dusuruldu (n=25, exp_R=-0.106)."""
    from .modules import default_modules
    isimler = {m.name for m in default_modules()}
    assert "NQ_ORB_STRONG_TREND" not in isimler
```

---

### BUG-2 — ORTA: Haftalık equity kalıcı değil → haftalık stop devre dışı

**Dosya**: `forward_ea/order_executor.py:121`

```python
# Şu an:
self._week_start_equity: dict[str, float] = {}  # sadece bellekte

# Karşılaştırma: günlük equity exec_day.json'a yazılıyor (satır 217-227)
# Haftalık için eşdeğer bir JSON dosyası YOK.
```

**Sorun**: `live_runner` Task Scheduler ile her 5 dakikada bir yeniden başlatılıyor. Her başlatmada `_week_start_equity` sıfırlanıyor. `_get_week_start_equity()` (satır 276-285) her başlatmada mevcut equity'yi hafta başı kabul ediyor → haftalık kayıp daima 0% görünüyor → `_weekly_dd_halt()` hiçbir zaman tetiklenemiyor.

**Günlük stop** doğru çalışıyor (`exec_day.json` ile kalıcı). **Haftalık stop** hiç çalışmıyor.

**Yapılacak**: `exec_day.json`'daki haftalık kısım gibi `_get_week_start_equity` metodunu diske yaz. `exec_day.json`'a haftalık alanı da ekle veya ayrı `exec_week.json` oluştur. Örnek:

```python
def _get_week_start_equity(self) -> float:
    account = self.client.account_info()
    if account is None:
        return 0.0
    year, week, _ = datetime.now(timezone.utc).isocalendar()
    key = f"{year}-W{week:02d}"
    week_file = self.state_dir / "exec_week.json"
    week_file.parent.mkdir(parents=True, exist_ok=True)
    if week_file.exists():
        data = json.loads(week_file.read_text(encoding="utf-8"))
    else:
        data = {}
    if key not in data:
        data[key] = account.equity
        week_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return account.equity
    return data[key]
```

**Not**: `_week_start_equity` instance dict'i (satır 121) bu değişiklikten sonra silinebilir.

---

### BUG-3 — DÜŞÜK: `cloud_runner._existing_keys` `oku_defter` kapısını atlıyor

**Dosya**: `forward_ea/cloud_runner.py:68-81`

```python
def _existing_keys(ledger_path: Path) -> set[tuple[str, str, str]]:
    ...
    old = pd.read_csv(ledger_path)  # ham read — şema doğrulaması yok
```

Bu fonksiyon `ledger.oku_defter` yerine doğrudan `pd.read_csv` kullanıyor. Eğer `cloud_ledger.csv`'de çakışan satırlar varsa `_existing_keys` bunu yakalamıyor; CSV tutarsız ise `KeyError` veriyor.

**Etki**: Düşük — `_existing_keys` yalnızca yinelenen kayıt önleme için. Kanıt kapısı (`oku_defter`) `birlesik_forward()` üzerinden tripwire testinden geçiyor. Ama tutarsızlık prensibine (tek okuyucu) aykırı.

**Yapılacak**: Opsiyonel iyileştirme — `pd.read_csv` yerine `ledger.oku_defter` çağrısını deneyip `ValueError` yakala, sadece `(module, symbol, entry_time)` setini döndür.

---

## Mimari notlar (GPT için bağlam)

### Tek kaynak prensibi (bu projede tekrar eden sorun)
Proje boyunca çok yerde aynı bilgi iki yerde tutulmuş ve biri güncellenmemiştir:
- Whitelist drift (2026-08-06): `risk.py` güncellendi, `order_executor.py`'deki kopya unutuldu
- `ExecConfig` risk politikası kopyası (kaldırıldı)
- Defterin beş okuyucusu (`oku_defter` ile birleştirildi)
- İki eşleştirici (tek `eslestir_bir_bir` ile birleştirildi)
- **Şimdi**: NQ_ORB demotion `risk.py` yorumuna ve CLAUDE.md'ye yazıldı ama `modules.py`'den kaldırılmadı

### `ledger.py` kanıt kapısı (fail-closed)
`oku_defter` → şema doğrula → değer doğrula → tekil hale getir.
Eksik kolon veya çakışan kayıt → `ValueError`. Sessiz geçiş yok.

### Defterlerin ayrılığı
- `forward_ledger.csv` — MT5 broker feed (yerel, referans)
- `cloud_ledger.csv` — bedava feed, GitHub Actions (ek kanıt)
- `diskresyoner_defter.csv` — elle yorum defteri (ayrı)

Bu üçü HİÇBİR ZAMAN birleştirilmez. `birlesik_forward()` yalnızca ilk ikisini MAX eşleşme ile birleştirir (aynı işlem iki kez sayılmaz).

### `order_executor` güvenceleri
- `LIVE_MODULES`: `risk.live_module_names()` TEK kaynaktan
- Lot hesabı: `risk_plan()` → `normal_usd` → `lot_for()` (broker tick_value ile)
- Düzleştirilmiş risk: boost (winner_pct) emir yolunda kasıtlı kullanılmıyor
- Günlük DD halt: `exec_day.json` ile kalıcı — çalışıyor
- Haftalık DD halt: bellek — çalışmıyor (BUG-2)

### GitHub Actions (`cloud_ledger.yml`)
- Saatte bir çalışıyor (cron `20 * * * *`)
- Push çakışmasında 3 deneme + rebase
- Hata → Telegram bildirimi
- `warmup_days` workflow_dispatch parametresi

### `diskresyoner.py` kuralları (kod zorunlu)
- Katman kapısı: ≥2/4 (narrative/hacim/trend/destek)
- Tez ≥20 karakter, çürüten ≥15 karakter zorunlu
- Solvency kapısı: risk_usd > (bakiye - 4500 - 100) → ValueError
- Durma kuralı: n≥20 ve exp_R<0 → `durma_tetik=True` (sadece gösterge, kilitleme koda eklenmemiş)

---

## Özet tablo

| # | Önem | Dosya | Satır | Sorun |
|---|------|-------|-------|-------|
| BUG-1 | KRİTİK | `modules.py` | 245-246 | NQ_ORB hâlâ default_modules'te, Telegram'a sinyal atıyor |
| BUG-2 | ORTA | `order_executor.py` | 121, 276 | Haftalık equity bellekte → haftalık stop devre dışı |
| BUG-3 | DÜŞÜK | `cloud_runner.py` | 68-81 | `_existing_keys` `oku_defter` yerine ham CSV okuyor |

BUG-1 en acil. Herhangi bir değişiklik öncesinde:
```bash
cd strategy-lab
python -m pytest intraday/ -q  # 400 passed, 3 skipped bekleneri
```
