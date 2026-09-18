"""Compact, delayed NQ chart for a Telegram discretionary watch card."""
from __future__ import annotations

from io import BytesIO
from zoneinfo import ZoneInfo

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from ..indicators import ema

NY = ZoneInfo("America/New_York")
TR = ZoneInfo("Europe/Istanbul")
WIDTH, HEIGHT = 900, 560
LEFT, TOP, RIGHT, BOTTOM = 60, 94, 840, 440


def _font(size: int):
    for name in ("DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _rth_vwap(bars: pd.DataFrame) -> pd.Series:
    local = bars.index.tz_convert(NY)
    minutes = local.hour * 60 + local.minute
    mask = ((local.date == local[-1].date()) &
            (minutes >= 9 * 60 + 30) & (minutes < 16 * 60))
    part = bars.loc[mask]
    if part.empty or part["volume"].isna().any() or (part["volume"] <= 0).any():
        return pd.Series(dtype=float)
    typical = (part["high"] + part["low"] + part["close"]) / 3
    return (typical * part["volume"]).cumsum() / part["volume"].cumsum()


def render_chart(bars: pd.DataFrame, *, level: float | None = None) -> bytes:
    """Render closed 15m candles, EMA20/50 and NY cash-session VWAP as PNG."""
    if len(bars) < 50 or bars.index.tz is None:
        raise ValueError("en az 50 zaman-dilimli kapali bar gerekli")
    for column in ("open", "high", "low", "close", "volume"):
        if column not in bars or bars[column].isna().any():
            raise ValueError(f"eksik/bozuk veri: {column}")
    visible = bars.tail(48)
    ema20 = ema(bars["close"], 20).reindex(visible.index)
    ema50 = ema(bars["close"], 50).reindex(visible.index)
    vwap = _rth_vwap(bars).reindex(visible.index)
    values = pd.concat([visible["high"], visible["low"], ema20, ema50, vwap]).dropna()
    low, high = float(values.min()), float(values.max())
    if low >= high:
        raise ValueError("grafik fiyat araligi yok")
    pad = max((high - low) * 0.07, 0.01)
    low, high = low - pad, high + pad
    show_level = level is not None and low <= level <= high

    image = Image.new("RGB", (WIDTH, HEIGHT), (17, 24, 39))
    draw = ImageDraw.Draw(image)
    title_font, body_font, small_font = _font(23), _font(17), _font(14)

    def x_pos(i: int) -> float:
        return LEFT + (i + 0.5) * (RIGHT - LEFT) / len(visible)

    def y_pos(value: float) -> float:
        return BOTTOM - (value - low) / (high - low) * (BOTTOM - TOP)

    draw.text((LEFT, 18), "NQ=F  |  15 dk  |  Mobil izleme", fill=(237, 241, 247), font=title_font)
    closed_tr = (visible.index[-1] + pd.Timedelta(minutes=15)).tz_convert(TR)
    draw.text((LEFT, 53), f"Son kapanan mum: {closed_tr:%d.%m %H:%M} TR  |  Yahoo gecikmeli veri",
              fill=(162, 176, 198), font=body_font)

    for step in range(5):
        price = low + (high - low) * step / 4
        y = y_pos(price)
        draw.line((LEFT, y, RIGHT, y), fill=(43, 53, 70), width=1)
        draw.text((RIGHT + 10, y - 9), f"{price:,.0f}", fill=(153, 167, 190), font=small_font)

    candle_width = max(3, int((RIGHT - LEFT) / len(visible) * 0.55))
    for i, row in enumerate(visible.itertuples()):
        x = x_pos(i)
        color = (56, 206, 155) if row.close >= row.open else (239, 105, 112)
        draw.line((x, y_pos(row.high), x, y_pos(row.low)), fill=color, width=2)
        a, b = y_pos(row.open), y_pos(row.close)
        draw.rectangle((x - candle_width / 2, min(a, b), x + candle_width / 2,
                        max(a, b) + 1), fill=color)

    for series, color, width in ((ema20, (246, 190, 72), 3),
                                 (ema50, (181, 138, 255), 3),
                                 (vwap, (65, 203, 232), 4)):
        points = [(x_pos(i), y_pos(float(value))) for i, value in enumerate(series)
                  if pd.notna(value)]
        if len(points) > 1:
            draw.line(points, fill=color, width=width, joint="curve")
    if show_level:
        y = y_pos(float(level))
        for x in range(LEFT, RIGHT, 18):
            draw.line((x, y, min(x + 9, RIGHT), y), fill=(235, 235, 235), width=2)
        draw.text((RIGHT - 115, y - 20), "Dun seviyesi", fill=(235, 235, 235), font=small_font)

    for i in (0, len(visible) // 2, len(visible) - 1):
        label = visible.index[i].tz_convert(TR).strftime("%H:%M")
        draw.text((x_pos(i) - 18, BOTTOM + 10), label, fill=(153, 167, 190), font=small_font)
    draw.text((LEFT, 488), "EMA20", fill=(246, 190, 72), font=body_font)
    draw.text((LEFT + 108, 488), "EMA50", fill=(181, 138, 255), font=body_font)
    draw.text((LEFT + 216, 488), "NY nakit VWAP", fill=(65, 203, 232), font=body_font)
    draw.text((LEFT, 523), "NQ grafigi Maven US100 emir fiyati degildir; MT5'te teyit et.",
              fill=(169, 183, 203), font=small_font)
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
