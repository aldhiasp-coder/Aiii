"""
Momentum indicators: RSI (Wilder's smoothing), MACD, Stochastic, CCI.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from app.core.exceptions import InsufficientDataError
from app.domain.indicator_models import IndicatorResult, Signal
from app.domain.models import Candle


def rsi(candles: Sequence[Candle], period: int, timeframe: str) -> IndicatorResult:
    """RSI dengan smoothing Wilder (bukan simple rolling mean) -- standar
    industri, konsisten dengan TradingView/MetaTrader."""
    if len(candles) < period + 1:
        raise InsufficientDataError(required=period + 1, available=len(candles))

    closes = pd.Series([c.close for c in candles], dtype="float64")
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder smoothing == EWM dengan alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    rsi_series = rsi_series.fillna(100)  # avg_loss == 0 -> RSI 100 (all gains)

    value = float(rsi_series.iloc[-1])

    if value >= 70:
        signal = Signal.OVERBOUGHT
        interp = f"RSI {value:.1f} berada di zona overbought (>=70) -- momentum bullish sudah ekstrem, waspada koreksi."
    elif value <= 30:
        signal = Signal.OVERSOLD
        interp = f"RSI {value:.1f} berada di zona oversold (<=30) -- momentum bearish sudah ekstrem, waspada rebound."
    elif value > 50:
        signal = Signal.BULLISH_MOMENTUM
        interp = f"RSI {value:.1f} di atas 50 -- momentum bullish, tetapi belum berada pada kondisi ekstrem."
    elif value < 50:
        signal = Signal.BEARISH_MOMENTUM
        interp = f"RSI {value:.1f} di bawah 50 -- momentum bearish, tetapi belum berada pada kondisi ekstrem."
    else:
        signal = Signal.NEUTRAL
        interp = f"RSI {value:.1f} tepat di titik netral 50."

    return IndicatorResult(
        name=f"RSI{period}",
        value=round(value, 2),
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(v, 2) for v in rsi_series.dropna().tolist()),
    )


def macd(
    candles: Sequence[Candle],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
    *,
    timeframe: str,
) -> IndicatorResult:
    if len(candles) < slow + signal_period:
        raise InsufficientDataError(
            required=slow + signal_period, available=len(candles)
        )

    closes = pd.Series([c.close for c in candles], dtype="float64")
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    macd_val = float(macd_line.iloc[-1])
    signal_val = float(signal_line.iloc[-1])
    hist_val = float(histogram.iloc[-1])
    hist_prev = float(histogram.iloc[-2]) if len(histogram) >= 2 else hist_val

    if macd_val > signal_val and hist_val > hist_prev:
        signal = Signal.BULLISH_MOMENTUM
        interp = "MACD line di atas signal line dan histogram melebar -- momentum bullish menguat."
    elif macd_val > signal_val:
        signal = Signal.BULLISH
        interp = "MACD line di atas signal line -- momentum bullish, tapi histogram mulai menyempit."
    elif macd_val < signal_val and hist_val < hist_prev:
        signal = Signal.BEARISH_MOMENTUM
        interp = "MACD line di bawah signal line dan histogram melebar ke bawah -- momentum bearish menguat."
    else:
        signal = Signal.BEARISH
        interp = "MACD line di bawah signal line -- momentum bearish, tapi histogram mulai menyempit."

    return IndicatorResult(
        name="MACD",
        value={"macd": round(macd_val, 8), "signal": round(signal_val, 8), "histogram": round(hist_val, 8)},
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(v, 8) for v in histogram.dropna().tolist()),
    )


def stochastic(
    candles: Sequence[Candle],
    k_period: int = 14,
    d_period: int = 3,
    *,
    timeframe: str,
) -> IndicatorResult:
    if len(candles) < k_period + d_period:
        raise InsufficientDataError(
            required=k_period + d_period, available=len(candles)
        )

    highs = pd.Series([c.high for c in candles], dtype="float64")
    lows = pd.Series([c.low for c in candles], dtype="float64")
    closes = pd.Series([c.close for c in candles], dtype="float64")

    lowest_low = lows.rolling(window=k_period).min()
    highest_high = highs.rolling(window=k_period).max()
    range_ = (highest_high - lowest_low).replace(0, np.nan)

    percent_k = 100 * (closes - lowest_low) / range_
    percent_d = percent_k.rolling(window=d_period).mean()

    k_val = float(percent_k.iloc[-1])
    d_val = float(percent_d.iloc[-1])

    if k_val >= 80:
        signal = Signal.OVERBOUGHT
        interp = f"Stochastic %K {k_val:.1f} berada di zona overbought (>=80)."
    elif k_val <= 20:
        signal = Signal.OVERSOLD
        interp = f"Stochastic %K {k_val:.1f} berada di zona oversold (<=20)."
    elif k_val > d_val:
        signal = Signal.BULLISH
        interp = f"%K ({k_val:.1f}) di atas %D ({d_val:.1f}) -- momentum jangka pendek bullish."
    else:
        signal = Signal.BEARISH
        interp = f"%K ({k_val:.1f}) di bawah %D ({d_val:.1f}) -- momentum jangka pendek bearish."

    return IndicatorResult(
        name=f"Stochastic({k_period},{d_period})",
        value={"k": round(k_val, 2), "d": round(d_val, 2)},
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(v, 2) for v in percent_k.dropna().tolist()),
    )


def cci(candles: Sequence[Candle], period: int = 20, *, timeframe: str) -> IndicatorResult:
    if len(candles) < period:
        raise InsufficientDataError(required=period, available=len(candles))

    typical_price = pd.Series(
        [(c.high + c.low + c.close) / 3 for c in candles], dtype="float64"
    )
    sma_tp = typical_price.rolling(window=period).mean()
    mean_dev = typical_price.rolling(window=period).apply(
        lambda x: np.mean(np.abs(x - x.mean())), raw=True
    )
    cci_series = (typical_price - sma_tp) / (0.015 * mean_dev.replace(0, np.nan))

    value = float(cci_series.iloc[-1])

    if value > 100:
        signal = Signal.OVERBOUGHT
        interp = f"CCI {value:.1f} > +100 -- kondisi overbought, potensi harga sudah bergerak jauh dari rata-rata."
    elif value < -100:
        signal = Signal.OVERSOLD
        interp = f"CCI {value:.1f} < -100 -- kondisi oversold, potensi harga sudah bergerak jauh di bawah rata-rata."
    elif value > 0:
        signal = Signal.BULLISH
        interp = f"CCI {value:.1f} positif -- harga di atas rata-rata jangka pendek."
    else:
        signal = Signal.BEARISH
        interp = f"CCI {value:.1f} negatif -- harga di bawah rata-rata jangka pendek."

    return IndicatorResult(
        name=f"CCI{period}",
        value=round(value, 2),
        signal=signal,
        interpretation=interp,
        timeframe=timeframe,
        series=tuple(round(v, 2) for v in cci_series.dropna().tolist()),
    )
