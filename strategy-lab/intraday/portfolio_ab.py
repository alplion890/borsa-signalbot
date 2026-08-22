"""Portfoy kompozisyonu A/B -- gercek parayla hangi moduller islem yapmali?

Spec: docs/superpowers/specs/2026-08-14-portfoy-kompozisyonu-design.md
Karar kurali, metrik ve portfoy listesi ORADA ve OLCUMDEN ONCE commit edildi
(5756c2b). Bu dosya yalnizca o kurali uygular; sonuca bakip esik/aday
degistirmek yasaktir.

Calistir:
    python -m intraday.portfolio_ab
"""
from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from pathlib import Path

import numpy as np
import pandas as pd

# --- taahhut edilmis kurallar (spec bolum 2) --------------------------------

CH_RISK = 0.015          # challenge normal risk
CH_RISK_AFTER_WIN = 0.03
CH_TARGET = 0.04         # +%4 gecis
CH_STOP = -0.08          # -%8 durma (Karar Kurali; Maven'in -%10'undan siki)
CH_MAX_TRADES = 500

FU_RISK = 0.005          # funded risk
FU_DAILY_LOSS = 0.04     # gunluk zarar limiti
FU_TRAILING_DD = 0.08    # tepeden trailing DD
FU_DAYS = 252            # 12 ay
TRADING_DAYS_WEEK = 5

LEDGER = (Path(__file__).resolve().parents[1] / "outputs" / "intraday" /
          "forward_ea" / "forward_ledger.csv")

def _load_ledger():
    """Backfill haric defter -- tek kapi (`forward_ea.ledger`)."""
    from .forward_ea.ledger import load_forward
    d = load_forward(LEDGER)
    d["exit_time"] = pd.to_datetime(d["exit_time"])
    return d


SWEEP_SYMBOLS = ["US100", "US500", "US30", "US2000", "UK100", "FRA40", "JAP225"]


# --- cekirdek: tek slot -----------------------------------------------------


def one_slot(df: pd.DataFrame) -> pd.DataFrame:
    """Ayni anda tek islem kuralini uygula (kronolojik, ilk gelen kazanir).

    Uygulanmazsa cok sembollu portfoyler sistematik olarak sisirilir --
    spec bolum 6.
    """
    out = []
    busy_until = None
    for _, row in df.sort_values("entry_time").iterrows():
        if busy_until is None or row["entry_time"] >= busy_until:
            out.append(row)
            busy_until = row["exit_time"]
    return pd.DataFrame(out).reset_index(drop=True) if out else df.iloc[:0]


# --- cekirdek: challenge fazi ----------------------------------------------


def challenge_equity_after(r_seq: np.ndarray) -> float:
    """Verilen R dizisinden sonraki ozkaynak orani (durdurma uygulanmadan).

    Risk kurali: normal %1.5; onceki KAPANAN islem kazandiysa %3.
    """
    eq = 1.0
    prev_win = False
    for r in r_seq:
        risk = CH_RISK_AFTER_WIN if prev_win else CH_RISK
        eq *= 1.0 + risk * float(r)
        prev_win = float(r) > 0
    return eq


def simulate_challenge(R: np.ndarray, n_paths: int, rng) -> np.ndarray:
    """Her yol icin challenge gecildi mi (bool dizi)."""
    eq = np.ones(n_paths)
    prev_win = np.zeros(n_paths, dtype=bool)
    passed = np.zeros(n_paths, dtype=bool)
    live = np.ones(n_paths, dtype=bool)
    for _ in range(CH_MAX_TRADES):
        if not live.any():
            break
        r = R[rng.integers(len(R), size=n_paths)]
        risk = np.where(prev_win, CH_RISK_AFTER_WIN, CH_RISK)
        eq = np.where(live, eq * (1.0 + risk * r), eq)
        prev_win = np.where(live, r > 0, prev_win)
        hit = live & (eq >= 1.0 + CH_TARGET)
        bust = live & (eq <= 1.0 + CH_STOP)
        passed |= hit
        live &= ~(hit | bust)
    return passed


# --- cekirdek: funded fazi --------------------------------------------------


def funded_path_survives(daily_returns: np.ndarray) -> bool:
    """Gunluk getiri dizisi (baslangica oran) verilen hesap hayatta kalir mi?

    Iki kural: gunluk zarar <= -%4 -> biter; tepeden fark >= %8 -> biter.
    Trailing TEPEDEN olculur, baslangictan degil.
    """
    eq = 1.0
    peak = 1.0
    for d in daily_returns:
        if float(d) <= -FU_DAILY_LOSS:
            return False
        eq += float(d)
        peak = max(peak, eq)
        if (peak - eq) >= FU_TRAILING_DD:
            return False
    return True


def simulate_funded(R: np.ndarray, trades_per_day: float, n_days: int,
                    n_paths: int, rng) -> np.ndarray:
    """Her yol icin funded fazinda hayatta kaldi mi (bool dizi)."""
    eq = np.ones(n_paths)
    peak = np.ones(n_paths)
    alive = np.ones(n_paths, dtype=bool)
    for _ in range(n_days):
        if not alive.any():
            break
        counts = rng.poisson(trades_per_day, size=n_paths)
        day = np.zeros(n_paths)
        for k in range(1, int(counts.max()) + 1 if counts.max() > 0 else 1):
            take = counts >= k
            if not take.any():
                continue
            day += np.where(take, R[rng.integers(len(R), size=n_paths)] * FU_RISK, 0.0)
        alive &= ~(day <= -FU_DAILY_LOSS)
        eq = np.where(alive, eq + day, eq)
        peak = np.maximum(peak, eq)
        alive &= ~((peak - eq) >= FU_TRAILING_DD)
    return alive


def chained_metric(R: np.ndarray, trades_per_week: float, n_paths: int,
                   rng) -> float:
    """P(challenge gec VE 12 ay funded'da hayatta kal) -- spec bolum 2."""
    if len(R) == 0 or trades_per_week <= 0:
        return 0.0
    passed = simulate_challenge(R, n_paths, rng)
    if not passed.any():
        return 0.0
    alive = simulate_funded(R, trades_per_week / TRADING_DAYS_WEEK, FU_DAYS,
                            n_paths, rng)
    return float((passed & alive).mean())


# --- veri kaynaklari --------------------------------------------------------

PORTFOLIOS = {
    "1 SWEEP tek sembol": {"sweep": ["US100"], "orb": False},
    "2 MEVCUT (SWEEP+NQ_ORB)": {"sweep": ["US100"], "orb": True},
    "3 SWEEP 7 sembol": {"sweep": SWEEP_SYMBOLS, "orb": False},
    "4 SWEEP 7 sembol+NQ_ORB": {"sweep": SWEEP_SYMBOLS, "orb": True},
}

_FWD_SWEEP = {
    "US100": "SWEEP_CORE_AVOID_MID_VWAP", "US500": "CAND_SWEEP_SP500",
    "US30": "CAND_SWEEP_US30", "US2000": "CAND_SWEEP_US2000",
    "UK100": "CAND_SWEEP_UK100", "FRA40": "CAND_SWEEP_FRA40",
    "JAP225": "CAND_SWEEP_JAP225",
}
_FWD_ORB = "NQ_ORB_STRONG_TREND"


def _pool(df: pd.DataFrame, span_weeks: float) -> tuple[np.ndarray, float]:
    """Tek-slot uygula, (R havuzu, islem/hafta) dondur."""
    if len(df) == 0:
        return np.array([]), 0.0
    kept = one_slot(df)
    return kept["r"].to_numpy(dtype=float), len(kept) / span_weeks


def build_forward() -> dict[str, tuple[np.ndarray, float]]:
    d = _load_ledger()
    span = (d["entry_time"].max() - d["entry_time"].min()).days / 7
    out = {}
    for name, cfg in PORTFOLIOS.items():
        mods = [_FWD_SWEEP[s] for s in cfg["sweep"]]
        if cfg["orb"]:
            mods.append(_FWD_ORB)
        out[name] = _pool(d[d["module"].isin(mods)], span)
    return out


def _hold_hours(family: str) -> np.ndarray:
    """Forward defterinden GERCEK tutma sureleri (saat).

    `simulate_trades` yalnizca (giris_zamani -> R) donduruyor, cikis zamani yok.
    Tek-slot filtresi cikis zamanina bagli oldugu icin sabit bir sayi uydurmak
    sonucu dogrudan kaydirir. Bunun yerine ayni modul ailesinin canli
    defterdeki ampirik tutma dagilimindan orneklenir.
    """
    d = _load_ledger()
    if family == "sweep":
        m = d["module"].str.contains("SWEEP") & ~d["module"].str.contains("ES_DIV")
    else:
        m = d["module"] == _FWD_ORB
    h = (d.loc[m, "exit_time"] - d.loc[m, "entry_time"]).dt.total_seconds() / 3600
    return h.to_numpy(dtype=float)


def build_backtest(days: int = 180, seed: int = 23
                   ) -> dict[str, tuple[np.ndarray, float]]:
    """MT5 backtest: 7 sembolde SWEEP + US100'de ORB. Gercek spread olculur."""
    from .multi_index_lab import _instrument, fetch, run_orb, run_sweep

    frames, costs = fetch(SWEEP_SYMBOLS, days)
    span = days / 7
    rng = np.random.default_rng(seed)
    h_sweep, h_orb = _hold_hours("sweep"), _hold_hours("orb")
    sweep, orb = {}, None

    def _exits(idx, holds):
        drawn = holds[rng.integers(len(holds), size=len(idx))]
        return idx + pd.to_timedelta(drawn, unit="h")

    for s, df5 in frames.items():
        inst = _instrument(s, costs[s], float(df5["close"].iloc[-1]))
        r = run_sweep(df5, inst)
        sweep[s] = pd.DataFrame({
            "entry_time": r.index, "exit_time": _exits(r.index, h_sweep),
            "r": r.to_numpy(), "module": f"SWEEP_{s}"})
        if s == "US100":
            ro = run_orb(df5, inst)
            orb = pd.DataFrame({
                "entry_time": ro.index, "exit_time": _exits(ro.index, h_orb),
                "r": ro.to_numpy(), "module": "NQ_ORB"})
    out = {}
    for name, cfg in PORTFOLIOS.items():
        parts = [sweep[s] for s in cfg["sweep"] if s in sweep]
        if cfg["orb"] and orb is not None:
            parts.append(orb)
        out[name] = _pool(pd.concat(parts) if parts else pd.DataFrame(), span)
    return out


# --- karar (spec bolum 4) ---------------------------------------------------

BASE = "2 MEVCUT (SWEEP+NQ_ORB)"


@dataclass(frozen=True)
class Verdict:
    name: str
    metric: float
    p_beats_base: float


def evaluate(pools: dict, n_boot: int = 300, n_paths: int = 1500,
             seed: int = 17) -> list[Verdict]:
    """Eslestirilmis bootstrap: her yinelemede TUM portfoyler ayni tohumla."""
    names = list(pools)
    draws = {n: [] for n in names}
    for b in range(n_boot):
        for n in names:
            R, rate = pools[n]
            if len(R) == 0:
                draws[n].append(0.0)
                continue
            rs = np.random.default_rng(seed + b)
            Rb = R[rs.integers(len(R), size=len(R))]       # havuzu yeniden ornekle
            draws[n].append(chained_metric(Rb, rate, n_paths,
                                           np.random.default_rng(seed + b)))
    base = np.array(draws[BASE])
    out = []
    for n in names:
        v = np.array(draws[n])
        out.append(Verdict(n, float(v.mean()),
                           float((v > base).mean()) if n != BASE else float("nan")))
    return out


def _report(label: str, pools: dict, verdicts: list[Verdict]) -> str | None:
    print("\n" + "=" * 78)
    print(f"  {label}")
    print("=" * 78)
    print(f"{'portfoy':<26}{'n':>5}{'exp_R':>9}{'isl/hf':>8}{'metrik':>9}{'P(>mevcut)':>12}")
    for v in verdicts:
        R, rate = pools[v.name]
        exp = f"{R.mean():+.3f}" if len(R) else "  --  "
        p = "  (kiyas)" if v.name == BASE else f"{v.p_beats_base*100:>10.1f}%"
        print(f"{v.name:<26}{len(R):>5}{exp:>9}{rate:>8.2f}{v.metric*100:>8.1f}%{p:>12}")
    winners = [v for v in verdicts if v.name != BASE and v.p_beats_base >= 0.95]
    if not winners:
        print("\n  -> Esigi (P>=%95) gecen portfoy YOK. Bu kaynakta degisiklik yok.")
        return None
    best = max(winners, key=lambda v: v.metric)
    print(f"\n  -> Esigi gecen: {[v.name for v in winners]}")
    print(f"  -> En yuksek metrik: {best.name}")
    return best.name


def main() -> None:
    print("PORTFOY KOMPOZISYONU A/B")
    print("Spec: docs/superpowers/specs/2026-08-14-portfoy-kompozisyonu-design.md")
    print("Metrik: P(challenge gec VE 12 ay funded'da hayatta kal)")
    print("Kural: P(aday>mevcut)>=%95, iki veri kaynaginda da. Beraberlik=degisiklik yok.")

    fwd = build_forward()
    w_fwd = _report("VERI A — forward defteri (durust, kucuk)", fwd, evaluate(fwd))

    print("\n  MT5'ten backtest verisi cekiliyor (7 sembol, gercek spread)...")
    bt = build_backtest()
    w_bt = _report("VERI B — MT5 backtest 6 ay, 7 sembol", bt, evaluate(bt))

    print("\n" + "=" * 78)
    print("  KARAR")
    print("=" * 78)
    if w_fwd is not None and w_fwd == w_bt:
        print(f"  Iki kaynakta da ayni kazanan: {w_fwd}")
        print("  -> TERFI EDILIR (spec bolum 7'ye gore baglanir).")
    else:
        print(f"  Veri A kazanani: {w_fwd or 'yok'}")
        print(f"  Veri B kazanani: {w_bt or 'yok'}")
        print("  -> Iki kaynak ortusmuyor veya esik gecilmedi.")
        print("  -> DEGISIKLIK YOK. Mevcut portfoy (SWEEP_CORE + NQ_ORB) kalir.")
    print()


if __name__ == "__main__":
    main()
