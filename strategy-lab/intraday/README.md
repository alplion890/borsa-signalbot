# Intraday Regime Router Lab

Ana hedef artik tek strateji bulmak degil:

```text
Rejim secici + kucuk strateji portfoyu + prop risk motoru
```

Guncel notlar:

```text
../REGIME_ROUTER_RUNBOOK.md
../FAILED_EXPERIMENTS.md
```

## Aktif stack

```text
fast_honest_core.py             Opsiyonel numba hiz cekirdegi
honest_engine.py                Muhafazakar bar-by-bar R backtest
sweep_regime_scan.py            NASDAQ100 sweep edge/regime ledger
internet_seed_strategies.py     ORB/London modullerini uretir
internet_seed_smart_run.py      Internet seed dar liste testi
internet_seed_regime_scan.py    ORB/London rejim ledger'i
wall_street_diagnosis.py        Edge nerede yasiyor otopsisi
regime_router_factory.py        Sweep + ORB + London router
regime_router_risk_cycle.py     1%->2% risk cycle testi
regime_router_risk_policy_scan.py
regime_router_winner_report.py
regime_router_final_tweak_scan.py
```

## Guncel finalist

```text
Policy: 09_hybrid_1_5_3_sweep_cap3

Normal trade: 1.5% risk
Kazanan trade sonrasi: 3.0%
Kayip sonrasi: tekrar 1.5%
Sweep trade: 2.25% base boost, maksimum 3.0% cap
```

## Finalist metrikleri

```text
Haftalik islem: 4.01
Win rate: 51.29%
Expectancy: +0.089R / trade
PF: 1.372
30g pass: 24.45%
Median pass: 16 gun
Daily DD fail: 1.24%
Total DD fail: 2.47%
```

## Calistirma

```powershell
cd C:\Users\quantum\OneDrive\Masaüstü\borsa\strategy-lab
python -m intraday.regime_router_factory
python -m intraday.regime_router_risk_policy_scan
python -m intraday.regime_router_winner_report
```

Final tweak scan checkpoint'lidir:

```powershell
python -m intraday.regime_router_final_tweak_scan
```

Kapanirsa ayni komut kaldigi yerden devam eder.

## Korunan ciktilar

```text
outputs/intraday/sweep_regime_ledger.csv
outputs/intraday/internet_seed_regime_ledgers.csv
outputs/intraday/wall_street_*.csv
outputs/intraday/regime_router_*.csv
```

## Silinen eski deneyler

Detayli liste:

```text
../FAILED_EXPERIMENTS.md
```

Kisa ozet:

```text
AMD/FVG ana strateji olmadi.
Crypto derivatives four-gate edge vermedi.
Day-filter tek basina prop gecirmedi.
Eski tek-strateji/vectorbt raporlari yerine regime router'a gecildi.
```
