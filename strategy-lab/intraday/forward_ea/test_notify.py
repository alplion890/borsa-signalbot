"""forward_ea.notify testleri."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from intraday.forward_ea.notify import notify_new_positions, build_message
from intraday.forward_ea.positions import PaperPosition


def _pos(module: str, symbol: str, minutes_ago: float,
         entry: float = 20000.0, sl: float = 20050.0, tp: float = 19900.0,
         weight: float = 1.0) -> PaperPosition:
    now = dt.datetime.now(dt.timezone.utc)
    return PaperPosition(
        module=module, symbol=symbol, direction=-1,
        entry_time=pd.Timestamp(now - dt.timedelta(minutes=minutes_ago)),
        entry=entry, sl=sl, tp=tp, weight=weight,
        max_hold_bars=48, cost_per_side=0.0001,
    )


def test_fresh_live_position_sends_message_with_card():
    outbox: list[str] = []
    sent = notify_new_positions(
        [_pos("SWEEP_CORE_AVOID_MID_VWAP", "NASDAQ100", minutes_ago=5)],
        send_fn=outbox.append,
    )
    assert len(sent) == 1 and len(outbox) == 1
    assert "MAVEN EMIR KARTI" in outbox[0]
    assert "US100" in outbox[0]
    assert "SELL" in outbox[0]


def test_candidate_position_never_reaches_telegram():
    """Aday moduller forward'da olculur ama TELEFONA CIKMAZ.

    Bu yol `_cycle`'in actigi tum pozisyonlari aliyordu -- adaylar dahil.
    Kanitlanmamis sinyalin telefona dusmesi BTC'de aylarca yasanan seydi.
    """
    outbox: list[str] = []
    sent = notify_new_positions(
        [_pos("CAND_SWEEP_SP500", "SP500", minutes_ago=5, weight=0.0)],
        send_fn=outbox.append,
    )
    assert sent == [] and outbox == []


def test_zero_weight_position_is_treated_as_candidate():
    """Isim kurali bozulsa bile weight=0.0 tek basina yeterli isaret."""
    outbox: list[str] = []
    sent = notify_new_positions(
        [_pos("ISIMSIZ_OLCUM_MODULU", "NASDAQ100", minutes_ago=5, weight=0.0)],
        send_fn=outbox.append,
    )
    assert sent == [] and outbox == []


def test_unknown_symbol_does_not_kill_the_whole_cycle():
    """Bilinmeyen sembol tum cevrimi cokertmemeli.

    build_message -> risk_plan -> lot_for -> _VALUE_PER_POINT[symbol].
    Tabloda olmayan sembol KeyError atar ve build_message ONCEDEN try
    disindaydi: tek bir modul tum turu cokertir, o turdaki OrderExecutor
    mutabakati hic calismazdi.

    NOT: yalnizca LIVE modullerde ulasilabilir. PAPER modulde risk 0'dir,
    `lot_for` daha _VALUE_PER_POINT'e bakmadan `risk_usd <= 0` ile doner --
    yani aday modullerin bilinmeyen sembolleri (US30/UK100/FRA40...) bugun
    kazara zararsiz. Kazayla degil, KURALLA korunmali: bu yuzden LIVE bir
    modul adiyla test ediliyor.
    """
    outbox: list[str] = []
    sent = notify_new_positions(
        [
            _pos("SWEEP_CORE_AVOID_MID_VWAP", "US30", minutes_ago=5),
            _pos("SWEEP_CORE_AVOID_MID_VWAP", "NASDAQ100", minutes_ago=5),
        ],
        send_fn=outbox.append,
    )
    # Ilki duser, ikincisi yine de gonderilir.
    assert len(sent) == 1 and len(outbox) == 1
    assert "US100" in outbox[0]


def test_failed_send_is_not_counted_as_sent():
    """Gonderim patlarsa mesaj "bildirildi" sayilmamali.

    Eski kodda `sent.append` except'in disindaydi: Telegram hatasi alinsa
    bile mesaj gonderilmis gibi raporlaniyordu.
    """
    def patla(_msg: str) -> None:
        raise RuntimeError("telegram down")

    sent = notify_new_positions(
        [_pos("NQ_ORB_STRONG_TREND", "NASDAQ100", minutes_ago=5)],
        send_fn=patla,
    )
    assert sent == []


def test_stale_backfill_position_is_skipped():
    outbox: list[str] = []
    sent = notify_new_positions(
        [_pos("NQ_ORB_STRONG_TREND", "NASDAQ100", minutes_ago=120)],
        send_fn=outbox.append,
    )
    assert sent == [] and outbox == []


def test_paper_module_message_has_no_card():
    now = dt.datetime.now(dt.timezone.utc)
    msg = build_message(
        _pos("EUR_LONDON_FADE_EMA", "EURUSD", minutes_ago=3,
             entry=1.095, sl=1.096, tp=1.093), now,
    )
    assert "paper" in msg.lower()
    assert "MAVEN EMIR KARTI" not in msg


def test_send_failure_does_not_raise():
    """Gonderim hatasi donguyu KIRMAMALI (asil amac), ama "bildirildi"
    de SAYILMAMALI -- eski hali `len(sent) == 1` bekliyordu, yani basarisiz
    gonderimi basarili raporluyordu. Sayim iddiasi
    test_failed_send_is_not_counted_as_sent'e tasindi."""
    def boom(_msg: str) -> None:
        raise RuntimeError("env eksik")

    notify_new_positions(                      # patlamadan donmeli
        [_pos("NQ_ORB_STRONG_TREND", "NASDAQ100", minutes_ago=5)],
        send_fn=boom,
    )
