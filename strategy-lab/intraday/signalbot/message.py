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
    "BTCUSDT_OF_ABSORPTION": "BTC absorption",
}

# symbol_key -> MavenTrade-Server broker sembol adi (MT5'te gorunen isim).
# NASDAQ100 broker'da US100 (bkz. forward_ea/README sembol duzeltmesi).
_MAVEN_SYMBOL = {
    "XAUUSD": "XAUUSD",
    "NASDAQ100": "US100",
    "SP500": "US500",
    "EURUSD": "EURUSD",
    "GBPUSD": "GBPUSD",
    "BTC": "BTCUSD",
}


def _fmt_offset(value: float) -> str:
    """Fark seviyesini enstrumanin buyuklugune gore yeterli basamakla yaz.

    Sabit `%+.1f` kullanmak endekste dogru ama FX'te FELAKET: EURUSD stop
    mesafesi 0.0011 mertebesinde, tek ondalikla "+0.0" yazilir ve kart
    kullanilamaz hale gelir. Esikler enstruman listesine degil buyuklugun
    kendisine bakar -- yeni sembol eklendiginde de dogru calisir.
    """
    size = abs(value)
    if size >= 100:
        return f"{value:+.1f}"
    if size >= 1:
        return f"{value:+.2f}"
    return f"{value:+.5f}"


def _offset_unit(symbol_key: str) -> str:
    """FX'te "puan" yaniltici (pip mi, fiyat mi?); duz "fiyat farki" denir."""
    return "fiyat farki" if symbol_key in {"EURUSD", "GBPUSD"} else "puan"


def _maven_order_card(*, symbol_key: str, direction: int, entry: float,
                      sl: float, tp: float, lot: float, risk_usd: float,
                      ref_close: float | None = None, tf: str = "") -> str:
    """MT5'e elle girilecek emrin kopyala-yapistir karti.

    Maven kurali: EA/bot yasak, emri SEN girersin. Kart sadece alanlari
    hazirlar. Duz ASCII, boru karakteri yok (telegram sade metin kurali).

    FIYATLAR NEDEN FARK OLARAK VERILIYOR (2026-08-06):
    Sinyal yfinance ^NDX ENDEKSINDEN uretiliyor, ama emir MT5'te US100 CFD'sine
    giriliyor. Iki seri ayni degil -- 30 gunluk olcum (feed_parity.py):
        basis (US100 - ^NDX) = -170.0 puan, std 34.9, gunluk kayma ~4.8 puan
    Yani kart ham endeks fiyatini yazsaydi, US100'de 170 puan (medyan stop
    111.8 puana gore ~1.5R) yanlis seviye vermis olurdu: BUY emri piyasanin
    cok ustunde buy-stop'a donusur, stop/hedef de kayar, R hesabi bozulur.
    Sabit 170 dusmek de cozum degil -- basis suruklenıyor, sessizce bozulur.

    Fark (delta) bicimi basis'ten BAGIMSIZ: iki serinin getiri korelasyonu
    0.9962, farklari cikardiktan sonra kalan artik gurultu std 0.030R
    (p95 0.063R) -- ihmal edilebilir. Sen grafikten P'yi okursun, basis
    ne olursa olsun seviye dogru cikar.
    """
    yon = "BUY" if direction == 1 else "SELL"
    sembol = _MAVEN_SYMBOL.get(symbol_key, symbol_key)
    head = (
        "\n\nMAVEN EMIR KARTI (elle gir, kopyala)\n"
        f"Sembol: {sembol}\n"
        f"Yon: {yon}\n"
    )
    if ref_close is None:
        seviye = (
            f"Giris: {entry:g} (retest bekle, market kovalama)\n"
            f"Stop: {sl:g}\n"
            f"Hedef: {tp:g}\n"
        )
    else:
        mum = f"son kapanan {tf} mumunun" if tf else "son kapanan mumun"
        d_entry, d_sl, d_tp = entry - ref_close, sl - ref_close, tp - ref_close
        birim = _offset_unit(symbol_key)
        seviye = (
            f"P = {sembol} grafiginde {mum} kapanisi\n"
            f"Giris: P {_fmt_offset(d_entry)} {birim} (retest bekle, market kovalama)\n"
            f"Stop: P {_fmt_offset(d_sl)} {birim}\n"
            f"Hedef: P {_fmt_offset(d_tp)} {birim}\n"
            f"NOT: seviyeler FARK olarak verildi. Sinyal endeks serisinden "
            f"geliyor, {sembol} ondan farkli fiyattadir; asagidaki ham "
            f"sayilari MT5'e YAZMA.\n"
            f"Ham endeks seviyeleri (sadece referans): giris {entry:g} "
            f"stop {sl:g} hedef {tp:g}\n"
        )
    return head + seviye + f"Lot: {lot:g}\nRisk: {risk_usd:g} dolar"


def format_signal(*, tier: Tier, module: str, symbol_key: str, direction: int,
                  entry: float, sl: float, tp: float, lot: float,
                  risk_usd: float, trt_time: str,
                  risk_plan: RiskPlan | None = None,
                  expected_delay_minutes: int = 0,
                  signal_age_minutes: float | None = None,
                  live_quote: LiveQuote | None = None,
                  live_quote_supported: bool = True,
                  data_source: str = "unknown",
                  ref_close: float | None = None,
                  tf: str = "") -> str:
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
                "Bu PAPER modul icin gercek risk sifir. "
                "Sadece izle ve performans defterine yaz."
            )
        elif risk_plan.normal_usd > 0 and risk_plan.normal_lot == 0:
            risk_text = (
                f"Planlanan risk {risk_plan.normal_usd:g} dolar fakat 0.01 minimum lot "
                "bu risk tavanini asiyor. Bu islemi gercek hesapta alma."
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
    if data_source == "yfinance":
        common_tail += " Mum verisi Yahoo Finance feed'inden."
    elif data_source == "binance":
        common_tail += " Mum verisi Binance public feed'inden."
    if live_quote is not None:
        risk_distance = abs(entry - sl)
        drift = live_quote.price - entry
        directional_r = direction * drift / risk_distance if risk_distance > 0 else 0.0
        direction_text = (
            f"{yon} yonune ilerlemis" if direction * drift > 0
            else "setup yonunun tersine gitmis" if direction * drift < 0
            else "giris seviyesinde"
        )
        quote_time = dt.datetime.fromtimestamp(
            live_quote.timestamp_ms / 1000, tz=dt.timezone.utc
        ).astimezone(dt.timezone(dt.timedelta(hours=3)))
        common_tail += (
            f" Finnhub anlik fiyat {live_quote.price:g}. Girise gore "
            f"{drift:+g} yani setup acisindan {directional_r:+.2f}R, "
            f"fiyat {direction_text}. "
            f"Canli fiyat saati {quote_time.hour:02d} {quote_time.minute:02d}."
        )
    elif expected_delay_minutes > 0 and not live_quote_supported:
        common_tail += (
            " Futures kontratiyla uyumsuz CFD/spot fiyat proxy'si bilincli olarak "
            "kullanilmadi. Mevcut fiyati Maven grafiginden kontrol et."
        )
    elif expected_delay_minutes > 0:
        common_tail += (
            " Finnhub canli fiyat gelmedi. Sinyal yine gecerli aday olarak "
            "gonderildi, Maven grafiginden mevcut fiyati kontrol et."
        )
    if tier is Tier.LIVE:
        # Ham endeks fiyatini duz metinde de SOYLEME: kart farkla calisirken
        # gövde "20020 ten gir" derse kullanici o sayiyi MT5'e yazar (US100 o
        # seviyeden ~170 puan uzakta). Iki yer ayni dili konusmali.
        if ref_close is None:
            seviye_cumlesi = (
                f"Yaklasik {entry:g} ten gir, stop {sl:g}, hedef {tp:g}."
            )
        else:
            seviye_cumlesi = (
                f"Seviyeler asagidaki kartta FARK olarak verildi "
                f"(giris {_fmt_offset(entry - ref_close)} "
                f"{_offset_unit(symbol_key)})."
            )
        msg = (
            f"{ad} {yon} sinyali geldi. {seviye_cumlesi} {common_tail} "
            "Retest girisi bekle, kirilimi kovalama."
        )
        # Emir karti: sadece gercek para izni + gecerli lot varsa.
        real_ok = risk_plan is None or (
            risk_plan.real_money_allowed
            and not (risk_plan.normal_usd > 0 and risk_plan.normal_lot == 0)
        )
        if real_ok and lot > 0:
            msg += _maven_order_card(
                symbol_key=symbol_key, direction=direction, entry=entry,
                sl=sl, tp=tp, lot=lot, risk_usd=risk_usd,
                ref_close=ref_close, tf=tf,
            )
        return msg
    return (
        f"Paper sinyali {ad} {yon}. Once chart ac ve setupi teyit et. "
        f"Yaklasik {entry:g} ten gir, stop {sl:g}, hedef {tp:g}. {common_tail}"
    )
