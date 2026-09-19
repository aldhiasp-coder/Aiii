"""
Trend indicators: SMA, EMA, VWAP.

Semua fungsi menerima `Sequence[Candle]` (urutan waktu naik, candle terlama
duluan) dan mengembalikan `IndicatorResult` sesuai kontrak spek poin 6.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from app.core.exceptions import InsufficientDataError
from app.domain.indicator_models import IndicatorResult, Signal
from app.domain.models import Candle


def _closes(candles: Sequence[Candle]) -> pd.Series:
    return pd.Series([c.close for c in candles], dtype="float64")


def sma(candles: Sequence[Candle], period: int, timeframe: str) -> IndicatorResult:
    if len(candles) < period:
        raise InsufficientDataError(required=period, available=len(candles))
    closes = _closes(candles)
    series = closes.rolling(window=period).mean()
    value = float(series.iloc[-1])
    price = closes.iloc[-1]

    if price > value * 1.001:
        signal = Signal.BULLISH
        interp = f"Harga berada di atas SMA{period}, mengindikasikan bias trend naik."
    elif price < value * 0.999:
        signal = Signal.BEARISH
        interp = f"Harga berada di bawah SMA{period}, mengindikasikan bias trend turun."
    else:
        signal = Signal.NEUTRAL
        interp = f"Harga berada dekat SMA{period}, belum ada bias trend yang jelas."

    return IndicatorResult(
        name=f"SMA{period}",
        value=round(value, 8),
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(v, 8) for v in series.dropna().tolist()),
    )


def ema(candles: Sequence[Candle], period: int, timeframe: str) -> IndicatorResult:
    if len(candles) < period:
        raise InsufficientDataError(required=period, available=len(candles))
    closes = _closes(candles)
    series = closes.ewm(span=period, adjust=False).mean()
    value = float(series.iloc[-1])
    price = closes.iloc[-1]

    if len(series) >= 2 and price > value and series.iloc[-1] > series.iloc[-2]:
        signal = Signal.BULLISH
        interp = (
            f"Price di atas EMA{period} dan EMA{period} naik -- momentum trend bullish."
        )
    elif len(series) >= 2 and price < value and series.iloc[-1] < series.iloc[-2]:
        signal = Signal.BEARISH
        interp = (
            f"Price di bawah EMA{period} dan EMA{period} turun -- momentum trend bearish."
        )
    else:
        signal = Signal.NEUTRAL
        interp = f"Price berada di sekitar EMA{period}, trend belum jelas arahnya."

    return IndicatorResult(
        name=f"EMA{period}",
        value=round(value, 8),
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(v, 8) for v in series.tolist()),
    )


def vwap(candles: Sequence[Candle], timeframe: str) -> IndicatorResult:
    """
    VWAP kumulatif atas jendela candle yang diberikan (bukan reset harian
    otomatis -- caller bertanggung jawab memotong candle ke sesi/hari yang
    diinginkan jika VWAP harian yang dimaksud).
    """
    if len(candles) < 1:
        raise InsufficientDataError(required=1, available=0)

    typical_price = np.array([(c.high + c.low + c.close) / 3 for c in candles])
    volume = np.array([c.volume for c in candles])
    cum_vol = np.cumsum(volume)
    cum_pv = np.cumsum(typical_price * volume)

    if cum_vol[-1] == 0:
        raise InsufficientDataError(required=1, available=0)  # volume nol, tidak valid

    vwap_series = cum_pv / np.where(cum_vol == 0, np.nan, cum_vol)
    value = float(vwap_series[-1])
    price = candles[-1].close

    if price > value * 1.001:
        signal = Signal.BULLISH
        interp = "Price berada di atas VWAP -- buyer membayar di atas harga rata-rata volume, tekanan beli dominan."
    elif price < value * 0.999:
        signal = Signal.BEARISH
        interp = "Price berada di bawah VWAP -- seller mendominasi relatif terhadap harga rata-rata volume."
    else:
        signal = Signal.NEUTRAL
        interp = "Price berada dekat VWAP, tidak ada dominasi buyer/seller yang jelas."

    return IndicatorResult(
        name="VWAP",
        value=round(value, 8),
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(float(v), 8) for v in vwap_series),
    )
