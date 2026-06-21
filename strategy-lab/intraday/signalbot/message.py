"""Telegram mesaji — sade Turkce duz yazi, emoji/sembol yigini yok."""
from __future__ import annotations
import datetime as dt

from .finnhub_live import LiveQuote
from .risk import RiskPlan, Tier

_HUMAN = {
    "GOLD_NY_ORB_TREND": "Gold ORB",
    "NQ_ORB_STRONG_TREND": "NQ ORB",
    "SWEEP_CORE_AVOID_MID_VWAP": "NQ sweep",
    "EUR_LONDON_FADE_EMA": "EUR London fade",
    "GBP_LONDON_STRONG_TREND": "GBP London trend",
    "SWEEP_ES_DIV": "NQ ES uyumsuzluk",
    "BTCUSDT_OF_ABSORPTION": "BTC absorption",
}


def format_signal(*, tier: Tier, module: str, symbol_key: str, direction: int,
                  entry: float, sl: float, tp: float, lot: float,
                  risk_usd: float, trt_time: str,
                  risk_plan: RiskPlan | None = None,
                  expected_delay_minutes: int = 0,
                  signal_age_minutes: float | None = None,
                  live_quote: LiveQuote | None = None) -> str:
    yon = "long" if direction == 1 else "short"
    ad = _HUMAN.get(module, module)
    if risk_plan is None:
        risk_text = f"Risk {risk_usd:g} dolar yani lot {lot:g}."
    elif abs(risk_plan.normal_lot - risk_plan.winner_lot) < 1e-9:
        risk_text = (
            f"Risk yuzde {risk_plan.normal_pct * 100:g} yani "
            f"{risk_plan.normal_usd:g} dolar ve lot {risk_plan.normal_lot:g}."
        )
    else:
        risk_text = (
            f"Normal risk {risk_plan.normal_usd:g} dolar lot {risk_plan.normal_lot:g}. "
            f"Onceki kapanan islem kazandiysa {risk_plan.winner_usd:g} dolar "
            f"lot {risk_plan.winner_lot:g}."
        )
    if risk_plan is not None:
        if not risk_plan.real_money_allowed:
            risk_text = (
                "Funded hesapta bu PAPER modul icin gercek risk sifir. "
                "Sadece izle ve performans defterine yaz."
            )
        if risk_plan.profile_key == "bnpl_challenge":
            risk_text += (
                f" Hizli challenge kilidi: ayni anda tek islem ve toplam acik risk "
                f"en fazla yuzde {risk_plan.max_open_risk_pct * 100:g}. "
                f"Gun zarari yuzde {risk_plan.daily_stop_pct * 100:g} olursa dur."
            )
        else:
            risk_text += (
                f" Funded kilidi: toplam acik risk en fazla yuzde "
                f"{risk_plan.max_open_risk_pct * 100:g}. Gun zarari yuzde "
                f"{risk_plan.daily_stop_pct * 100:g}, hafta zarari yuzde "
                f"{risk_plan.weekly_stop_pct * 100:g} olursa dur. "
                "Kazanc sonrasi risk artirma."
            )
            if risk_plan.daily_profit_cap_pct is not None:
                risk_text += (
                    f" Gun kari yuzde {risk_plan.daily_profit_cap_pct * 100:g} "
                    "olunca yeni islem acma."
                )
            if risk_plan.consistency_day_share_pct is not None:
                risk_text += (
                    f" Tek gun kari toplam payout karinin yuzde "
                    f"{risk_plan.consistency_day_share_pct * 100:g} ini gecmesin."
                )
            if risk_plan.payout_buffer_pct is not None:
                risk_text += (
                    f" Payout icin once en az yuzde "
                    f"{risk_plan.payout_buffer_pct * 100:g} kar tamponu biriktir."
                )
    common_tail = (
        f"{risk_text} Saat {trt_time}. Acik islemin varsa veya fiyat giristen "
        "uzaklastiysa alma."
    )
    if expected_delay_minutes > 0 or signal_age_minutes is not None:
        age = signal_age_minutes if signal_age_minutes is not None else expected_delay_minutes
        common_tail += (
            f" Setup verisi yaklasik {age:.0f} dakika onceki kapanmis mumdan."
        )
    if live_quote is not None:
        risk_distance = abs(entry - sl)
        drift = live_quote.price - entry
        drift_r = drift / risk_distance if risk_distance > 0 else 0.0
        direction_text = (
            "long yonune ilerlemis" if direction * drift > 0
            else "setup yonunun tersine gitmis" if direction * drift < 0
            else "giris seviyesinde"
        )
        quote_time = dt.datetime.fromtimestamp(
            live_quote.timestamp_ms / 1000, tz=dt.timezone.utc
        ).astimezone(dt.timezone(dt.timedelta(hours=3)))
        common_tail += (
            f" Finnhub anlik fiyat {live_quote.price:g}. Girise gore "
            f"{drift:+g} yani {drift_r:+.2f}R, fiyat {direction_text}. "
            f"Canli fiyat saati {quote_time.hour:02d} {quote_time.minute:02d}."
        )
    elif expected_delay_minutes > 0:
        common_tail += (
            " Finnhub canli fiyat gelmedi. Sinyal yine gecerli aday olarak "
            "gonderildi, Maven grafiginden mevcut fiyati kontrol et."
        )
    if tier is Tier.LIVE:
        return (
            f"{ad} {yon} sinyali geldi. Yaklasik {entry:g} ten gir, "
            f"stop {sl:g}, hedef {tp:g}. {common_tail} "
            "Retest girisi bekle, kirilimi kovalama."
        )
    return (
        f"Paper sinyali {ad} {yon}. Once chart ac ve setupi teyit et. "
        f"Yaklasik {entry:g} ten gir, stop {sl:g}, hedef {tp:g}. {common_tail}"
    )
