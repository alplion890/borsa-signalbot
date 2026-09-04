from intraday.signalbot.message import format_signal
from intraday.signalbot.finnhub_live import LiveQuote
from intraday.signalbot.risk import Tier
from intraday.signalbot.risk import risk_plan


def test_live_gold_message():
    msg = format_signal(
        tier=Tier.LIVE,
        module="GOLD_NY_ORB_TREND",
        symbol_key="XAUUSD",
        direction=1,
        entry=4225,
        sl=4214,
        tp=4247,
        lot=0.5,
        risk_usd=75.0,
        trt_time="16:42"
    )
    assert "long" in msg
    assert "4225" in msg
    assert "4214" in msg
    assert "4247" in msg
    assert msg.count("|") == 0
    assert "retest" in msg.lower()


def test_paper_eur_message():
    msg = format_signal(
        tier=Tier.PAPER,
        module="EUR_LONDON_FADE_EMA",
        symbol_key="EURUSD",
        direction=-1,
        entry=1.0950,
        sl=1.0960,
        tp=1.0930,
        lot=0.1,
        risk_usd=50.0,
        trt_time="10:15"
    )
    assert "paper" in msg.lower()
    assert ("teyit" in msg.lower()) or ("kontrol" in msg.lower())


def test_delayed_futures_message_has_live_price_guard():
    msg = format_signal(
        tier=Tier.LIVE,
        module="GOLD_NY_ORB_TREND",
        symbol_key="XAUUSD",
        direction=1,
        entry=3000,
        sl=2990,
        tp=3010,
        lot=0.07,
        risk_usd=75,
        trt_time="16 45",
        expected_delay_minutes=10,
    )
    assert "10 dakika onceki" in msg
    assert "Finnhub canli fiyat gelmedi" in msg
    assert "Maven" in msg


def test_live_quote_is_compared_in_r_units():
    msg = format_signal(
        tier=Tier.LIVE,
        module="GOLD_NY_ORB_TREND",
        symbol_key="XAUUSD",
        direction=1,
        entry=3000,
        sl=2990,
        tp=3010,
        lot=0.07,
        risk_usd=75,
        trt_time="16 45",
        signal_age_minutes=15,
        live_quote=LiveQuote("XAUUSD", "OANDA:XAU_USD", 3003, 1781800000000),
    )
    assert "15 dakika onceki" in msg
    assert "Finnhub anlik fiyat 3003" in msg
    assert "setup acisindan +0.30R" in msg
    assert "long yonune ilerlemis" in msg


def test_short_favorable_quote_uses_short_direction_and_positive_r():
    msg = format_signal(
        tier=Tier.LIVE,
        module="NQ_ORB_STRONG_TREND",
        symbol_key="NASDAQ100",
        direction=-1,
        entry=30600,
        sl=30750,
        tp=30300,
        lot=0.02,
        risk_usd=75,
        trt_time="18 01",
        live_quote=LiveQuote(
            "NASDAQ100", "TEST:NQ", 30525, 1781800000000
        ),
    )
    assert "setup acisindan +0.50R" in msg
    assert "short yonune ilerlemis" in msg


def test_incompatible_futures_proxy_is_explained_without_finnhub_price():
    msg = format_signal(
        tier=Tier.LIVE,
        module="NQ_ORB_STRONG_TREND",
        symbol_key="NASDAQ100",
        direction=-1,
        entry=30600,
        sl=30750,
        tp=30300,
        lot=0.02,
        risk_usd=75,
        trt_time="18 01",
        expected_delay_minutes=10,
        live_quote_supported=False,
    )
    assert "uyumsuz CFD/spot fiyat proxy'si" in msg
    assert "Finnhub anlik fiyat" not in msg


def test_funded_message_contains_locked_stops_and_consistency():
    plan = risk_plan(
        phase="bnpl_funded", balance=5000, module_name="GOLD_NY_ORB_TREND",
        module_weight=1.0, symbol_key="XAUUSD", entry=3000, sl=2990,
    )
    msg = format_signal(
        tier=Tier.LIVE, module="GOLD_NY_ORB_TREND", symbol_key="XAUUSD",
        direction=1, entry=3000, sl=2990, tp=3015,
        lot=plan.normal_lot, risk_usd=plan.normal_usd,
        risk_plan=plan, trt_time="16 45",
    )
    assert "Funded kilidi" in msg
    assert "Kazanc sonrasi risk artirma" in msg
    assert "Gun kari yuzde 0.5" in msg
    assert "yuzde 18" in msg
    assert "yuzde 2.5 kar tamponu" in msg


def test_paper_message_forces_zero_real_risk():
    """Gold challenge'da da PAPER: kart gercek risk sifir demeli."""
    plan = risk_plan(
        phase="bnpl_challenge", balance=5000, module_name="GOLD_NY_ORB_TREND",
        module_weight=1.0, symbol_key="XAUUSD", entry=3000, sl=2990,
    )
    msg = format_signal(
        tier=Tier.PAPER, module="GOLD_NY_ORB_TREND", symbol_key="XAUUSD",
        direction=1, entry=3000, sl=2990, tp=3015,
        lot=plan.normal_lot, risk_usd=plan.normal_usd,
        risk_plan=plan, trt_time="16 45",
    )
    assert "gercek risk sifir" in msg
    assert "Sadece izle" in msg


def test_message_blocks_trade_when_minimum_lot_exceeds_risk():
    """Stop cok genisse %1 risk 0.01 lotun altina duser -> islem alinmamali."""
    plan = risk_plan(
        phase="bnpl_challenge", balance=5000,
        module_name="SWEEP_CORE_AVOID_MID_VWAP", module_weight=1.0,
        symbol_key="NASDAQ100", entry=20000, sl=19000,
    )
    assert plan.normal_usd > 0 and plan.normal_lot == 0
    msg = format_signal(
        tier=Tier.LIVE, module="NQ_ORB_STRONG_TREND", symbol_key="NASDAQ100",
        direction=1, entry=20000, sl=19000, tp=21500,
        lot=plan.normal_lot, risk_usd=plan.normal_usd,
        risk_plan=plan, trt_time="16 45",
    )
    assert "minimum lot" in msg
    assert "gercek hesapta alma" in msg


def test_live_message_has_maven_order_card():
    plan = risk_plan(
        phase="bnpl_challenge", balance=5000, module_name="SWEEP_CORE_AVOID_MID_VWAP",
        module_weight=1.0, symbol_key="NASDAQ100", entry=20000, sl=19950,
    )
    msg = format_signal(
        tier=Tier.LIVE, module="NQ_ORB_STRONG_TREND", symbol_key="NASDAQ100",
        direction=-1, entry=20000, sl=20050, tp=19900,
        lot=plan.normal_lot, risk_usd=plan.normal_usd,
        risk_plan=plan, trt_time="16 45",
    )
    assert "MAVEN EMIR KARTI" in msg
    assert "US100" in msg          # broker sembol adi, symbol_key degil
    assert "SELL" in msg
    assert "Giris: 20000" in msg
    assert "Stop: 20050" in msg
    assert "Hedef: 19900" in msg
    assert "Lot:" in msg
    assert msg.count("|") == 0


def test_order_card_writes_levels_as_offsets_when_ref_close_given():
    """Sinyal ^NDX'ten, emir US100'e girilir -- ham endeks fiyati YAZILMAMALI.

    Olculdu (feed_parity.py, 30 gun): basis -170 puan, gunluk kayma ~4.8.
    Ham fiyat yazilirsa US100'de ~1.5R yanlis seviye verir.
    """
    plan = risk_plan(
        phase="bnpl_challenge", balance=5000, module_name="SWEEP_CORE_AVOID_MID_VWAP",
        module_weight=1.0, symbol_key="NASDAQ100", entry=20000, sl=19950,
    )
    msg = format_signal(
        tier=Tier.LIVE, module="NQ_ORB_STRONG_TREND", symbol_key="NASDAQ100",
        direction=1, entry=20020, sl=19950, tp=20125,
        lot=plan.normal_lot, risk_usd=plan.normal_usd,
        risk_plan=plan, trt_time="16 45", ref_close=20000.0, tf="5m",
    )
    assert "Giris: P +20.00 puan" in msg
    assert "Stop: P -50.00 puan" in msg
    assert "Hedef: P +125.0 puan" in msg
    assert "son kapanan 5m mumunun" in msg
    assert "MT5'e YAZMA" in msg
    # Kopyalanabilir alan olarak ham fiyat gorunmemeli.
    assert "Giris: 20020" not in msg
    # Govde de ayni dili konusmali: "20020 ten gir" DEMEMELI.
    assert "20020 ten gir" not in msg


def test_card_states_target_size_in_R_and_dollars():
    """Kart "bu islem ne kazandirir" sorusunu cevaplamali.

    R olmadan iki sinyal kiyaslanamaz: 1.4R'lik ORB ile 7R'lik sweep
    kartta ayni gorunurdu.
    """
    plan = risk_plan(
        phase="bnpl_challenge", balance=5000, module_name="SWEEP_CORE_AVOID_MID_VWAP",
        module_weight=1.0, symbol_key="NASDAQ100", entry=20000, sl=19950,
    )
    msg = format_signal(
        tier=Tier.LIVE, module="NQ_ORB_STRONG_TREND", symbol_key="NASDAQ100",
        direction=1, entry=20000, sl=19950, tp=20100,   # 50 risk / 100 odul
        lot=plan.normal_lot, risk_usd=plan.normal_usd,
        risk_plan=plan, trt_time="16 45",
    )
    assert "Hedef buyuklugu: 2.0R" in msg
    assert "+150 dolar" in msg          # 75 dolar risk x 2.0R
    assert "-75" in msg


def test_card_warns_when_stop_is_inside_the_noise():
    """Dar stop R'yi payda kucukluguyle sisirir -- kart bunu soylemeli.

    Gercek ornek (2026-08-07, CAND_SWEEP_SP500): SP500 7719'da giris,
    stop 7714.65 -> 4.35 puan, fiyatin binde 0.56'si. Planlanan RR 7.5,
    gerceklesen 7.2R. Canlida o stopu spread+gurultu rutin supurur.
    """
    msg = format_signal(
        tier=Tier.LIVE, module="NQ_ORB_STRONG_TREND", symbol_key="NASDAQ100",
        direction=1, entry=7719.0, sl=7714.65, tp=7751.7,
        lot=0.5, risk_usd=75.0, trt_time="17 00",
    )
    assert "Hedef buyuklugu: 7.5R" in msg
    assert "stop cok dar" in msg
    assert "gerekcesi SAYMA" in msg


def test_normal_stop_gets_no_narrow_warning():
    msg = format_signal(
        tier=Tier.LIVE, module="NQ_ORB_STRONG_TREND", symbol_key="NASDAQ100",
        direction=1, entry=20000, sl=19900, tp=20200,
        lot=0.3, risk_usd=75.0, trt_time="17 00",
    )
    assert "stop cok dar" not in msg


def test_paper_signal_also_states_R():
    """Kagit sinyalinde kart cikmaz; R tek gorunur olcek olarak govdede."""
    msg = format_signal(
        tier=Tier.PAPER, module="GOLD_NY_ORB_TREND", symbol_key="XAUUSD",
        direction=1, entry=3000, sl=2990, tp=3015,
        lot=0.0, risk_usd=0.0, trt_time="16 45",
    )
    assert "Hedef buyuklugu 1.5R" in msg


def test_order_card_offsets_keep_precision_on_fx():
    """FX farklari 0.001 mertebesinde -- sabit tek ondalik kart'i cope atardi.

    EURUSD stop mesafesi defterde ~0.0011. `%+.1f` ile hepsi "+0.0" yazilir,
    kart kullanilamaz. Endeks ve FX ayni bicimlendiriciden gecer.
    """
    msg = format_signal(
        tier=Tier.LIVE, module="EUR_LONDON_FADE_EMA", symbol_key="EURUSD",
        direction=1, entry=1.09550, sl=1.09440, tp=1.09715,
        lot=0.1, risk_usd=75.0, trt_time="10 15",
        ref_close=1.09500, tf="5m",
    )
    assert "Giris: P +0.00050" in msg
    assert "Stop: P -0.00060" in msg
    assert "+0.0 " not in msg          # basamak kaybi olmamali
    assert "fiyat farki" in msg        # FX'te "puan" yaniltici


def test_order_card_falls_back_to_absolute_without_ref_close():
    """ref_close yoksa eski davranis korunur (forward EA/testler kirilmasin)."""
    msg = format_signal(
        tier=Tier.LIVE, module="NQ_ORB_STRONG_TREND", symbol_key="NASDAQ100",
        direction=1, entry=20020, sl=19950, tp=20125,
        lot=0.1, risk_usd=75.0, trt_time="16 45",
    )
    assert "Giris: 20020" in msg
    assert "puan" not in msg.split("MAVEN EMIR KARTI")[1]


def test_paper_message_has_no_order_card():
    msg = format_signal(
        tier=Tier.PAPER, module="EUR_LONDON_FADE_EMA", symbol_key="EURUSD",
        direction=-1, entry=1.0950, sl=1.0960, tp=1.0930,
        lot=0.1, risk_usd=50.0, trt_time="10 15",
    )
    assert "MAVEN EMIR KARTI" not in msg


def test_zero_lot_live_message_has_no_order_card():
    msg = format_signal(
        tier=Tier.LIVE, module="GOLD_NY_ORB_TREND", symbol_key="XAUUSD",
        direction=1, entry=3000, sl=2990, tp=3015,
        lot=0.0, risk_usd=75.0, trt_time="16 45",
    )
    assert "MAVEN EMIR KARTI" not in msg
