"""Coklu-karsilastirma duzeltmesi: bir aday, KAC aday tarandigini bilerek hala iyi mi?

Neden var
---------
Mevcut kapilar (regime_router_overfit_validation._decision, GA fitness gate)
esik tabanli: exp_R >= 0.14, yil-yil pozitif, vs. Hicbiri "bu sonuca ulasmak
icin kac kombinasyon denedim" bilgisini kullanmiyor. 65 TV adayi, 45 inside-day
hucresi, yuzlerce ORB varyanti tarandiginda en iyinin iyi gorunmesi
GARANTIDIR -- gercek edge olmasa bile.

Bu modul o eksigi kapatir (Lopez de Prado):
  - probabilistic_sharpe_ratio : SR > esik olma olasiligi (n, carpiklik, basiklik dahil)
  - expected_max_sharpe        : N adet SIFIR-edge adaydan en iyisinin beklenen SR'si
  - deflated_sharpe_ratio      : PSR, esigi yukaridaki sans-beklentisine cekerek
  - probability_of_backtest_overfitting : CSCV ile "IS'te en iyi olan OOS'ta
                                          medyanin altina duser mi" olasiligi

Girdi her yerde islem basi R serisi (honest_engine.simulate_trades ciktisi) ya
da onun donemsel toplami. Anlam:
  DSR >= 0.95  -> arama boyutuna ragmen anlamli
  DSR <  0.95  -> "en iyi"ligi tesadufle aciklanabilir, forward testsiz benimseme
  PBO <= 0.20  -> secim prosedurunun kendisi saglikli
  PBO >  0.50  -> secim proseduru gurultu seciyor, esikleri degil prosedura bak
"""
from __future__ import annotations

from itertools import combinations
from typing import Mapping

import numpy as np
import pandas as pd
from scipy.stats import norm

EULER_MASCHERONI = 0.5772156649015329

__all__ = [
    "align_trials",
    "deflated_from_trials",
    "deflated_sharpe_ratio",
    "expected_max_sharpe",
    "probabilistic_sharpe_ratio",
    "probability_of_backtest_overfitting",
    "sharpe",
]


def sharpe(r: pd.Series) -> float:
    """Islem basi Sharpe (yillandirilmamis): ortalama / standart sapma.

    R cinsinden calisildigi icin yillandirma bilerek yapilmaz -- modullerin
    islem frekansi cok farkli (NQ_ORB haftada ~2, SWEEP_CORE ayda ~1) ve
    yillandirma seyrek modulu haksiz sisirir.
    """
    x = pd.Series(r).dropna()
    if len(x) < 2:
        return float("nan")
    sd = float(x.std(ddof=1))
    if not np.isfinite(sd) or sd < 1e-12:  # sabit seri; float artigi 0 sayilir
        return float("nan")
    return float(x.mean()) / sd


def probabilistic_sharpe_ratio(r: pd.Series, sr_benchmark: float = 0.0) -> float:
    """PSR: gercek SR'nin `sr_benchmark`'i astigi olasilik.

    Normal-olmayan getiri dagilimini cezalandirir: negatif carpiklik ve kalin
    kuyruk guveni dusurur. SWEEP_ES_DIV tipi "cok kucuk kayip, nadir buyuk
    kayip" profilleri tam burada yakalanir.
    """
    x = pd.Series(r).dropna()
    n = len(x)
    sr = sharpe(x)
    if n < 3 or np.isnan(sr):
        return float("nan")
    skew = float(x.skew())
    kurt = float(x.kurtosis()) + 3.0  # pandas fazlalik basiklik dondurur
    denom = 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr**2
    if denom <= 0.0:
        return float("nan")
    z = (sr - sr_benchmark) * np.sqrt(n - 1) / np.sqrt(denom)
    return float(norm.cdf(z))


def expected_max_sharpe(n_trials: int, sr_variance: float) -> float:
    """N adet SIFIR-edge adayin en iyisinden beklenen SR (sans esigi).

    `sr_variance` = denenen adaylarin SR'lerinin varyansi. Cok aday + yuksek
    dagilim => sirf sans eseri yuksek SR beklenir; asilmasi gereken esik budur.
    """
    if n_trials <= 1 or sr_variance <= 0.0:
        return 0.0
    sd = np.sqrt(sr_variance)
    q1 = norm.ppf(1.0 - 1.0 / n_trials)
    q2 = norm.ppf(1.0 - 1.0 / (n_trials * np.e))
    return float(sd * ((1.0 - EULER_MASCHERONI) * q1 + EULER_MASCHERONI * q2))


def deflated_sharpe_ratio(r: pd.Series, n_trials: int, sr_variance: float) -> float:
    """DSR: PSR, esigi `expected_max_sharpe` sans seviyesine cekilmis hali.

    0.95 ustu = arama boyutuna ragmen anlamli.
    """
    return probabilistic_sharpe_ratio(r, expected_max_sharpe(n_trials, sr_variance))


def deflated_from_trials(trials: Mapping[str, pd.Series]) -> dict:
    """Taranan TUM adaylari ver; en iyisini secip DSR'sini hesaplar.

    Kritik kullanim kurali: `trials` icine sadece finalistleri degil, taramada
    denenen her kombinasyonu koy. Eksik birakilan her aday DSR'yi yukari
    sasirtir -- yani kendini kandirir.
    """
    if not trials:
        raise ValueError("trials bos olamaz")
    srs = {name: sharpe(s) for name, s in trials.items()}
    valid = {k: v for k, v in srs.items() if not np.isnan(v)}
    if not valid:
        return {"best": None, "sharpe": float("nan"), "dsr": float("nan"),
                "n_trials": len(trials), "sr_variance": float("nan"),
                "sr_threshold": float("nan"), "trades": 0}
    best = max(valid, key=lambda k: valid[k])
    sr_variance = float(np.var(list(valid.values()), ddof=1)) if len(valid) > 1 else 0.0
    n_trials = len(trials)
    return {
        "best": best,
        "sharpe": round(valid[best], 4),
        "dsr": round(deflated_sharpe_ratio(trials[best], n_trials, sr_variance), 4),
        "n_trials": n_trials,
        "sr_variance": round(sr_variance, 6),
        "sr_threshold": round(expected_max_sharpe(n_trials, sr_variance), 4),
        "trades": int(pd.Series(trials[best]).dropna().shape[0]),
    }


def align_trials(trials: Mapping[str, pd.Series], freq: str = "W") -> pd.DataFrame:
    """Farkli zamanlarda isleyen aday defterlerini ortak donemsel matrise cevirir.

    PBO, adaylari ayni satirlarda karsilastirmak zorunda. Islemi olmayan donem
    NaN degil 0.0R sayilir -- "o hafta islem yok" = "o hafta kazanc yok".
    """
    if not trials:
        raise ValueError("trials bos olamaz")
    cols = {
        name: pd.Series(s).dropna().resample(freq).sum()
        for name, s in trials.items()
    }
    out = pd.concat(cols, axis=1)
    out.columns = list(trials.keys())
    return out.fillna(0.0).sort_index()


def probability_of_backtest_overfitting(
    matrix: pd.DataFrame, n_splits: int = 8
) -> dict:
    """CSCV ile PBO: IS'te secilen aday OOS'ta medyanin altina dusme olasiligi.

    Esikleri degil SECIM PROSEDURUNU test eder. Yuksek PBO = "en iyiyi sec"
    yaklasimin gurultu seciyor demektir; tek bir adayin metrigini duzelterek
    cozulmez.
    """
    if matrix.shape[1] < 2:
        raise ValueError("PBO icin en az 2 aday gerekir")
    if n_splits % 2 != 0:
        raise ValueError("n_splits cift olmali (yari IS / yari OOS)")
    if len(matrix) < n_splits * 2:
        raise ValueError(f"donem sayisi {n_splits * 2} altinda, PBO guvenilmez")

    blocks = np.array_split(np.arange(len(matrix)), n_splits)
    half = n_splits // 2
    values = matrix.to_numpy(dtype=float)
    n_trials = matrix.shape[1]
    logits: list[float] = []

    for is_blocks in combinations(range(n_splits), half):
        oos_blocks = [b for b in range(n_splits) if b not in is_blocks]
        is_rows = np.concatenate([blocks[b] for b in is_blocks])
        oos_rows = np.concatenate([blocks[b] for b in oos_blocks])
        is_score = _block_score(values[is_rows])
        oos_score = _block_score(values[oos_rows])
        if np.all(np.isnan(is_score)) or np.all(np.isnan(oos_score)):
            continue
        best = int(np.nanargmax(is_score))
        # OOS sirasi: 1 = en kotu, n_trials = en iyi
        order = pd.Series(oos_score).rank(method="average", na_option="bottom")
        w = float(order.iloc[best]) / (n_trials + 1.0)
        w = min(max(w, 1e-9), 1.0 - 1e-9)
        logits.append(float(np.log(w / (1.0 - w))))

    if not logits:
        return {"pbo": float("nan"), "n_combinations": 0, "median_logit": float("nan")}
    arr = np.asarray(logits)
    return {
        "pbo": round(float((arr <= 0.0).mean()), 4),
        "n_combinations": len(arr),
        "median_logit": round(float(np.median(arr)), 4),
    }


def _block_score(block: np.ndarray) -> np.ndarray:
    """Bir zaman blogunda aday basi skor (Sharpe). Sabit seri -> nan."""
    mean = np.nanmean(block, axis=0)
    sd = np.nanstd(block, axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(sd > 0, mean / sd, np.nan)
