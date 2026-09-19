from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from app.core.exceptions import InsufficientDataError
from app.domain.indicator_models import IndicatorResult, Signal
from app.domain.models import Candle


def obv(candles: Sequence[Candle], *, timeframe: str) -> IndicatorResult:
    if len(candles) < 2:
        raise InsufficientDataError(required=2, available=len(candles))

    closes = np.array([c.close for c in candles])
    volumes = np.array([c.volume for c in candles])
    direction = np.sign(np.diff(closes))
    direction = np.insert(direction, 0, 0)  # candle pertama tidak punya arah
    obv_series = np.cumsum(direction * volumes)

    value = float(obv_series[-1])
    # trend OBV: bandingkan slope beberapa candle terakhir
    lookback = min(10, len(obv_series) - 1)
    slope = obv_series[-1] - obv_series[-1 - lookback]

    if slope > 0:
        signal = Signal.BULLISH
        interp = "OBV naik -- volume beli kumulatif mendominasi, mendukung konfirmasi trend naik."
    elif slope < 0:
        signal = Signal.BEARISH
        interp = "OBV turun -- volume jual kumulatif mendominasi, mendukung konfirmasi trend turun."
    else:
        signal = Signal.NEUTRAL
        interp = "OBV mendatar -- tidak ada dominasi volume beli/jual yang jelas."

    return IndicatorResult(
        name="OBV",
        value=round(value, 2),
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(float(v), 2) for v in obv_series),
    )


def volume_ma(candles: Sequence[Candle], period: int = 20, *, timeframe: str) -> IndicatorResult:
    if len(candles) < period:
        raise InsufficientDataError(required=period, available=len(candles))

    volumes = pd.Series([c.volume for c in candles], dtype="float64")
    ma_series = volumes.rolling(window=period).mean()
    value = float(ma_series.iloc[-1])
    current_volume = volumes.iloc[-1]
    ratio = current_volume / value if value else 0.0

    if ratio >= 2.0:
        signal = Signal.EXPANDING
        interp = f"Volume saat ini {ratio:.1f}x rata-rata {period} candle terakhir -- lonjakan volume signifikan (anomaly)."
    elif ratio <= 0.5:
        signal = Signal.CONTRACTING
        interp = f"Volume saat ini hanya {ratio:.1f}x rata-rata {period} candle terakhir -- partisipasi pasar rendah."
    else:
        signal = Signal.NEUTRAL
        interp = f"Volume saat ini {ratio:.1f}x rata-rata {period} candle terakhir -- dalam rentang normal."

    return IndicatorResult(
        name=f"VolumeMA{period}",
        value=round(value, 2),
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(v, 2) for v in ma_series.dropna().tolist()),
    )
