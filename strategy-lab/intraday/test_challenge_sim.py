import pandas as pd

from intraday.challenge_sim import (
    MavenRules,
    RiskPolicy,
    simulate_path,
    summarize,
)


def _trades(r_values):
    idx = pd.date_range("2026-01-01", periods=len(r_values), freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "module": ["GOLD_NY_ORB_TREND"] * len(r_values),
            "weighted_r": r_values,
        },
        index=idx,
    )


def test_maven_rules_match_pay_after_pass():
    rules = MavenRules()
    assert rules.target_balance == 5200.0
    assert rules.breach_balance == 4500.0
    assert rules.daily_drawdown_pct is None
    assert rules.min_trading_days == 0
    assert rules.max_trading_days is None


def test_path_passes_at_four_percent():
    result = simulate_path(
        _trades([1.0, 1.0, 1.0, 1.0]),
        pd.Timestamp("2026-01-01", tz="UTC"),
        RiskPolicy("fixed_1", 0.01),
        validate_vectorbt=False,
    )
    assert result["result"] == "pass"
    assert result["trades"] == 4


def test_path_breaches_static_ten_percent():
    result = simulate_path(
        _trades([-1.0] * 11),
        pd.Timestamp("2026-01-01", tz="UTC"),
        RiskPolicy("fixed_1", 0.01),
        validate_vectorbt=False,
    )
    assert result["result"] == "max_drawdown"


def test_no_daily_drawdown_breach():
    result = simulate_path(
        _trades([-3.0, 4.0]),
        pd.Timestamp("2026-01-01", tz="UTC"),
        RiskPolicy("fixed_1", 0.01),
        validate_vectorbt=False,
    )
    assert result["result"] != "max_drawdown"


def test_summary_reports_pass_fail_open():
    paths = pd.DataFrame(
        {
            "result": ["pass", "max_drawdown", "open", "pass"],
            "days": [10, 20, 30, 14],
            "trades": [5, 8, 9, 7],
            "max_drawdown_pct": [2.0, 10.0, 4.0, 3.0],
        }
    )
    out = summarize(paths, RiskPolicy("x", 0.01), 30)
    assert out["pass_pct"] == 50.0
    assert out["fail_pct"] == 25.0
    assert out["open_pct"] == 25.0


# --- portfoy etiketleri risk.py ile senkron kalmali -----------------------
#
# 2026-08-28 denetiminde bulundu: "forward_verified_2" portfoyu
# GOLD_NY_ORB_TREND + NQ_ORB_STRONG_TREND olarak SABIT yazilmisti. Etiket
# 2026-08-06'da dogruydu; o tarihten sonra (a) defter backfill'den temizlendi
# ve rakamlar degisti, (b) GOLD emekli edildi, (c) NQ_ORB dusurme esigine
# 3 islem kaldi. Yani "forward dogrulanmis" diye etiketlenen kume, defterdeki
# EN KOTU iki modulu gosterir olmustu.
#
# Ayni hata sinifi bu projede daha once ucusu: whitelist'in ikinci kopyasi,
# ExecConfig'in kendi risk politikasi, defterin bes ayri okuyucusu. Cozum hep
# ayni: tek kaynak. Portfoy artik risk.py'den turuyor.


def test_canli_portfoy_risk_py_den_TURUYOR_sabit_liste_degil(monkeypatch):
    """Sabit modul listesi tier degisince sessizce yanlislasir.

    DAVRANIS TESTI (Hermes yeniden denetimi 2026-08-29): eski hali
    `inspect.getsource()` ile KAYNAK METNI okuyordu -- yani "risk.py'den
    turuyor" iddiasini degil, o metnin yazildigini sinaiyordu. Simdi
    `live_module_names` degistirilip `compare_bot_portfolios`'un GERCEKTEN
    hangi islemleri canli portfoye koydugu olculuyor.
    """
    import pandas as pd

    from . import challenge_sim
    from .signalbot.risk import live_module_names

    assert live_module_names(), "risk.py bos LIVE listesi donduruyor"

    trades = pd.DataFrame([
        {"module": "AYYY", "entry_time": pd.Timestamp("2026-08-01"), "r": 1.0},
        {"module": "BXXX", "entry_time": pd.Timestamp("2026-08-02"), "r": -1.0},
        {"module": "SWEEP_ES_DIV", "entry_time": pd.Timestamp("2026-08-03"), "r": 0.5},
    ])
    monkeypatch.setattr(challenge_sim, "live_module_names", lambda: ["AYYY"])

    sira: list[list[str]] = []

    def sahte_run_scan(portfolio_trades, **kw):
        sira.append(sorted(portfolio_trades["module"].unique()))
        return pd.DataFrame([{"policy": "p", "horizon_days": 30}]), pd.DataFrame()

    monkeypatch.setattr(challenge_sim, "run_scan", sahte_run_scan)
    challenge_sim.compare_bot_portfolios(trades, horizons=(30,),
                                         validate_vectorbt=False)
    assert sira[-1] == ["AYYY"], (
        f"canli portfoy risk.py'den turemiyor: {sira[-1]}")
