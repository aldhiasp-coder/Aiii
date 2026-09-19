"""
Exception hierarchy untuk seluruh sistem.

Dipisah per kategori sesuai spek poin 34 (ERROR HANDLING) supaya API layer
bisa memetakan tiap exception ke HTTP status + pesan yang jelas ke frontend,
dan supaya satu provider yang gagal tidak meng-crash seluruh dashboard.
"""

from __future__ import annotations


class MarketDataError(Exception):
    """Base class untuk semua error yang berasal dari market data layer."""


class ProviderTimeoutError(MarketDataError):
    """Request ke provider melebihi batas waktu."""

    def __init__(self, provider: str, symbol: str, timeout_seconds: float) -> None:
        self.provider = provider
        self.symbol = symbol
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"[{provider}] Timeout setelah {timeout_seconds}s saat mengambil {symbol}"
        )


class ProviderRateLimitError(MarketDataError):
    """Provider mengembalikan rate limit (HTTP 429 atau setara)."""

    def __init__(self, provider: str, retry_after_seconds: float | None = None) -> None:
        self.provider = provider
        self.retry_after_seconds = retry_after_seconds
        msg = f"[{provider}] Rate limit tercapai"
        if retry_after_seconds is not None:
            msg += f", coba lagi dalam {retry_after_seconds}s"
        super().__init__(msg)


class InvalidSymbolError(MarketDataError):
    """Symbol tidak dikenal/tidak didukung oleh provider."""

    def __init__(self, provider: str, symbol: str) -> None:
        self.provider = provider
        self.symbol = symbol
        super().__init__(f"[{provider}] Symbol tidak valid: {symbol!r}")


class UnsupportedTimeframeError(MarketDataError):
    """Timeframe yang diminta tidak didukung provider dan tidak aman diturunkan."""

    def __init__(self, provider: str, timeframe: str) -> None:
        self.provider = provider
        self.timeframe = timeframe
        super().__init__(
            f"[{provider}] Timeframe tidak didukung: {timeframe!r}"
        )


class ProviderOutageError(MarketDataError):
    """Provider mengembalikan error 5xx / tidak bisa dihubungi sama sekali."""

    def __init__(self, provider: str, detail: str) -> None:
        self.provider = provider
        self.detail = detail
        super().__init__(f"[{provider}] Provider outage: {detail}")


class MalformedResponseError(MarketDataError):
    """Response provider tidak sesuai schema yang diharapkan (tidak bisa dinormalisasi)."""

    def __init__(self, provider: str, detail: str) -> None:
        self.provider = provider
        self.detail = detail
        super().__init__(f"[{provider}] Response tidak sesuai schema: {detail}")


class InsufficientDataError(MarketDataError):
    """Data historis tidak cukup untuk menghitung sesuatu (mis. indikator butuh N candle)."""

    def __init__(self, required: int, available: int) -> None:
        self.required = required
        self.available = available
        super().__init__(
            f"Butuh minimal {required} candle, tersedia {available}"
        )
