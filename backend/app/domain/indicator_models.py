from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Signal(str, Enum):
    STRONG_BULLISH = "strong_bullish"
    BULLISH_MOMENTUM = "bullish_momentum"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    BEARISH_MOMENTUM = "bearish_momentum"
    STRONG_BEARISH = "strong_bearish"
    OVERBOUGHT = "overbought"
    OVERSOLD = "oversold"
    EXPANDING = "expanding"
    CONTRACTING = "contracting"


@dataclass(frozen=True, slots=True)
class IndicatorResult:
    """
    Bentuk output wajib untuk SEMUA indikator (spek poin 6):
    tidak boleh hanya angka mentah, harus ada signal + interpretation
    berbahasa natural yang bisa langsung dikonsumsi AI reasoning engine
    atau ditampilkan di UI.
    """

    name: str
    value: float | dict[str, float]
    signal: Signal
    interpretation: str
    timeframe: str
    series: Optional[tuple[float, ...]] = None  # nilai historis, untuk overlay chart
