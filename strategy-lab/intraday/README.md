# Intraday Lab

Bu klasor **arastirma** katmani: strateji arar, backtest eder, elenenlerin
kaydini tutar. Canli/karar katmani burada DEGIL:

```text
intraday/signalbot/     Telegram sinyali (GitHub Actions, bedava veri)
intraday/forward_ea/    Forward olcum defteri (MT5 + bulut) -- KARAR BURAYA BAKAR
intraday/mt5_bridge/    Broker koprusu, feed paritesi
```

> **Guncel durum bu dosyada DEGIL.** Modul tier'lari, risk politikasi ve
> "hangi sinyale girilir" karari surekli degisiyor; tek gecerli kaynak
> `forward_ea/README.md` + Obsidian vault (`Borsa MOC`). Asagisi laboratuvarin
> nasil calistigidir, ne karar verildigi degil.

## Cekirdek

```text
honest_engine.py                Muhafazakar bar-by-bar R backtest -- KARAR MOTORU
fast_honest_core.py             Opsiyonel numba hiz cekirdegi
config.py                       INSTRUMENTS: maliyet, seans, tick
indicators.py                   atr, swing, rolling high/low
data.py                         Dukascopy/cache okuma
overfit_stats.py                DSR / PSR / PBO (scipy gerektirir)
```

**Kural:** karar her zaman `honest_engine.simulate_trades` ile verilir.
vectorbt yalnizca hizli tarama icindi ve `from_signals` sl/tp doldurmasi
iyimser cikti (NASDAQ sweep vectorbt'te +0.10..+0.33R, dogru modelde
-0.027R). Bu ders MT5 forward testinde ikinci kez dogrulandi.

## Strateji ureticileri

```text
internet_seed_strategies.py     ORB/London modulleri (canli portfoyun kaynagi)
regime_router_factory.py        Sweep + ORB + London router
btc_cvd_sweep.py                BTC order flow (forward'da curudu)
intermarket_divergence.py       NQ/ES divergence (SWEEP_ES_DIV -- elendi)
```

## Denetim ve A/B

```text
overfit_audit.py                DSR/PBO denetimi
portfolio_ab.py                 Portfoy kompozisyonu A/B
fill_model_ab.py                Dolum modeli A/B (1m intrabar)
challenge_sim.py                Challenge Monte Carlo
funded_sim.py                   Funded faz simulasyonu
liquidity_profiler.py           Parite karakter/likidite haritasi
inside_day_lab.py               Inside-day iddiasi (curutuldu)
```

## Calistirma

```powershell
cd C:\Users\quantum\OneDrive\Masaüstü\borsa\strategy-lab
python -m pytest intraday/ -q          # once testler
python -m intraday.overfit_audit       # istatistik denetimi
python -m intraday.portfolio_ab        # portfoy A/B
```

MT5 gerektiren isler icin venv: `%USERPROFILE%\vectorbt-lab\.venv\Scripts\python.exe`

## Korunan ciktilar

```text
outputs/intraday/forward_ea/forward_ledger.csv    yeniden URETILEMEZ
outputs/intraday/forward_ea/cloud_ledger.csv      yeniden URETILEMEZ
outputs/intraday/forward_ea/icra_defteri.csv      yeniden URETILEMEZ
outputs/intraday/sweep_regime_ledger.csv          arastirma ciktisi
outputs/intraday/regime_router_*.csv              arastirma ciktisi
```

Geri kalan `outputs/` icerigi backtest kosumundan yeniden uretilebilir ve
gitignore'dadir.

## Elenen yaklasimlar

Ayrintili gerekce Obsidian vault'ta (`Borsa - Strategy Lab`, `Borsa - Sans mi
Edge mi`, `Borsa - Inside Day Sahte Edge`). Kisa liste:

```text
AMD/FVG bagimsiz edge vermedi.
FX/kripto/SP500'e sweep edge'i tasinmadi.
Meta-labeling (RandomForest) ve Kronos transformer: OOS negatif.
Gun filtreleri (dow=X) overfit cikti; post-hoc filtre bu projede YASAK.
Tek-strateji vectorbt raporlari yerine honest_engine + forward defteri.
```
