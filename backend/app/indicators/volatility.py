from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from app.core.exceptions import InsufficientDataError
from app.domain.indicator_models import IndicatorResult, Signal
from app.domain.models import Candle


def atr(candles: Sequence[Candle], period: int = 14, *, timeframe: str) -> IndicatorResult:
    if len(candles) < period + 1:
        raise InsufficientDataError(required=period + 1, available=len(candles))

    highs = pd.Series([c.high for c in candles], dtype="float64")
    lows = pd.Series([c.low for c in candles], dtype="float64")
    closes = pd.Series([c.close for c in candles], dtype="float64")
    prev_close = closes.shift(1)

    true_range = pd.concat(
        [
            highs - lows,
            (highs - prev_close).abs(),
            (lows - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr_series = true_range.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    value = float(atr_series.iloc[-1])
    price = closes.iloc[-1]
    atr_pct = (value / price) * 100 if price else 0.0

    # Bandingkan ATR saat ini dengan rata-rata ATR pada window yang sama
    # untuk menentukan apakah volatilitas sedang expanding/contracting.
    avg_atr = float(atr_series.dropna().mean())
    if value > avg_atr * 1.2:
        signal = Signal.EXPANDING
        interp = f"ATR{period} {value:.6g} ({atr_pct:.2f}% dari harga) -- volatilitas sedang melebar di atas rata-rata historisnya."
    elif value < avg_atr * 0.8:
        signal = Signal.CONTRACTING
        interp = f"ATR{period} {value:.6g} ({atr_pct:.2f}% dari harga) -- volatilitas sedang menyempit di bawah rata-rata historisnya."
    else:
        signal = Signal.NEUTRAL
        interp = f"ATR{period} {value:.6g} ({atr_pct:.2f}% dari harga) -- volatilitas berada dalam rentang normal."

    return IndicatorResult(
        name=f"ATR{period}",
        value=round(value, 8),
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(v, 8) for v in atr_series.dropna().tolist()),
    )


def bollinger_bands(
    candles: Sequence[Candle], period: int = 20, num_std: float = 2.0, *, timeframe: str
) -> IndicatorResult:
    if len(candles) < period:
        raise InsufficientDataError(required=period, available=len(candles))

    closes = pd.Series([c.close for c in candles], dtype="float64")
    middle = closes.rolling(window=period).mean()
    std = closes.rolling(window=period).std(ddof=0)
    upper = middle + num_std * std
    lower = middle - num_std * std

    price = closes.iloc[-1]
    upper_val = float(upper.iloc[-1])
    lower_val = float(lower.iloc[-1])
    middle_val = float(middle.iloc[-1])
    bandwidth = (upper_val - lower_val) / middle_val if middle_val else 0.0

    if price >= upper_val:
        signal = Signal.OVERBOUGHT
        interp = f"Price ({price:.6g}) menyentuh/menembus upper band ({upper_val:.6g}) -- volatil, berpotensi overextended."
    elif price <= lower_val:
        signal = Signal.OVERSOLD
        interp = f"Price ({price:.6g}) menyentuh/menembus lower band ({lower_val:.6g}) -- volatil, berpotensi overextended ke bawah."
    else:
        pct_position = (price - lower_val) / (upper_val - lower_val) if upper_val != lower_val else 0.5
        signal = Signal.NEUTRAL
        interp = f"Price berada di {pct_position*100:.0f}% posisi antara lower dan upper band (bandwidth {bandwidth*100:.2f}%)."

    return IndicatorResult(
        name=f"BollingerBands{period}",
        value={"upper": round(upper_val, 8), "middle": round(middle_val, 8), "lower": round(lower_val, 8)},
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(v, 8) for v in middle.dropna().tolist()),
    )
