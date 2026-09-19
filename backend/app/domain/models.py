"""
Internal normalized domain models.

Semua provider (Binance, TwelveData, dst) WAJIB memetakan response mentahnya
ke model-model di sini sebelum data dipakai oleh layer manapun di atasnya
(indicator engine, structure engine, AI reasoning engine).

Ini adalah implementasi nyata dari MarketSnapshot yang didefinisikan di
spesifikasi (poin 5 - DATA NORMALIZATION). Menggunakan stdlib `dataclasses`
karena `pydantic` tidak terpasang di environment ini; struktur & validasi
manualnya dibuat setara dengan yang pydantic lakukan (lihat __post_init__).
Saat di-deploy ke project nyata dengan pydantic tersedia, class ini bisa
dipetakan 1:1 ke `BaseModel` tanpa mengubah call-site.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class AssetClass(str, Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"


class DataStatus(str, Enum):
    LIVE = "LIVE"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


# Timeframe -> durasi dalam detik. Hanya timeframe yang benar-benar
# didukung provider yang boleh dipakai (lihat providers/base.py).
TIMEFRAME_SECONDS: dict[str, int] = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1H": 3600,
    "2H": 7200,
    "4H": 14400,
    "6H": 21600,
    "12H": 43200,
    "1D": 86400,
    "1W": 604800,
}


@dataclass(frozen=True, slots=True)
class Candle:
    """Satu candle OHLCV yang sudah dinormalisasi."""

    timestamp: int  # unix epoch (detik), waktu open candle, UTC
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.high < self.low:
            raise ValueError(
                f"Candle tidak valid: high ({self.high}) < low ({self.low}) "
                f"pada timestamp {self.timestamp}"
            )
        if not (self.low <= self.open <= self.high):
            raise ValueError(
                f"Candle tidak valid: open ({self.open}) di luar rentang "
                f"[{self.low}, {self.high}] pada timestamp {self.timestamp}"
            )
        if not (self.low <= self.close <= self.high):
            raise ValueError(
                f"Candle tidak valid: close ({self.close}) di luar rentang "
                f"[{self.low}, {self.high}] pada timestamp {self.timestamp}"
            )
        if self.volume < 0:
            raise ValueError(f"Volume tidak boleh negatif: {self.volume}")


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """
    Bentuk internal universal untuk satu simbol pada satu titik waktu.
    Semua layer di atas provider (indicators, structure, AI) hanya boleh
    bergantung pada bentuk ini -- TIDAK PERNAH pada format API eksternal.
    """

    symbol: str
    asset_class: AssetClass
    timestamp: int  # unix epoch detik, waktu snapshot diambil
    price: float
    timeframe: str
    ohlcv: tuple[Candle, ...]
    source: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume_24h: Optional[float] = None
    percentage_change_24h: Optional[float] = None
    status: DataStatus = DataStatus.LIVE
    fetched_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if self.timeframe not in TIMEFRAME_SECONDS:
            raise ValueError(
                f"Timeframe tidak dikenal: {self.timeframe!r}. "
                f"Harus salah satu dari {sorted(TIMEFRAME_SECONDS)}"
            )
        if self.price <= 0:
            raise ValueError(f"Price harus positif, dapat: {self.price}")
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError(
                f"Bid ({self.bid}) tidak boleh lebih besar dari ask ({self.ask})"
            )

    @property
    def spread(self) -> Optional[float]:
        if self.bid is None or self.ask is None:
            return None
        return round(self.ask - self.bid, 10)

    @property
    def age_seconds(self) -> float:
        now = datetime.now(timezone.utc)
        return (now - self.fetched_at).total_seconds()

    def resolved_status(self, stale_after_seconds: float = 15.0) -> DataStatus:
        """Status aktual berdasarkan umur data -- lihat spek poin 33/34."""
        if self.status == DataStatus.UNAVAILABLE:
            return DataStatus.UNAVAILABLE
        return (
            DataStatus.LIVE
            if self.age_seconds <= stale_after_seconds
            else DataStatus.STALE
        )
