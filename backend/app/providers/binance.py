"""
Binance REST provider -- implementasi nyata dari MarketDataProvider.

Endpoint yang dipakai (public, tidak butuh API key untuk market data):
  - GET /api/v3/ticker/24hr?symbol=...   -> harga + 24h stats
  - GET /api/v3/klines?symbol=...&interval=...&limit=...  -> OHLCV

Referensi resmi: https://binance-docs.github.io/apidocs/spot/en/
(Tidak diverifikasi live di sandbox ini karena network egress dimatikan --
lihat tests/test_binance_provider.py yang memvalidasi parsing/normalisasi
terhadap sample response asli Binance yang dipakai sebagai fixture, di-mock
lewat `requests.Session` sehingga tidak butuh network untuk lulus test.)
"""

from __future__ import annotations

import time
from typing import Any, Optional

import requests

from app.core.exceptions import (
    InvalidSymbolError,
    MalformedResponseError,
    ProviderOutageError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    UnsupportedTimeframeError,
)
from app.domain.models import AssetClass, Candle, DataStatus, MarketSnapshot
from app.providers.base import MarketDataProvider

BASE_URL = "https://api.binance.com"

# Binance native kline intervals -> internal timeframe label.
# Hanya interval yang benar-benar didukung Binance yang dimasukkan di sini
# (tidak ada 2H/6H/12H native di Binance spot klines -> tidak diklaim).
_INTERVAL_MAP: dict[str, str] = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1H": "1h",
    "4H": "4h",
    "1D": "1d",
    "1W": "1w",
}


class BinanceProvider(MarketDataProvider):
    name = "Binance"
    supported_timeframes = frozenset(_INTERVAL_MAP.keys())
    asset_classes = frozenset({AssetClass.CRYPTO})

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout_seconds: float = 5.0,
        base_url: str = BASE_URL,
    ) -> None:
        self._session = session or requests.Session()
        self._timeout = timeout_seconds
        self._base_url = base_url

    # -- public API ---------------------------------------------------

    def get_snapshot(self, symbol: str) -> MarketSnapshot:
        raw = self._request(
            "/api/v3/ticker/24hr", params={"symbol": self._normalize_symbol(symbol)}
        )
        return self._parse_ticker(symbol, raw)

    def get_ohlcv(
        self, symbol: str, timeframe: str, limit: int = 200
    ) -> MarketSnapshot:
        if timeframe not in _INTERVAL_MAP:
            raise UnsupportedTimeframeError(self.name, timeframe)
        if not (1 <= limit <= 1000):
            raise ValueError("limit harus di antara 1 dan 1000 (batas Binance)")

        interval = _INTERVAL_MAP[timeframe]
        raw = self._request(
            "/api/v3/klines",
            params={
                "symbol": self._normalize_symbol(symbol),
                "interval": interval,
                "limit": limit,
            },
        )
        candles = self._parse_klines(raw)
        last_close = candles[-1].close if candles else 0.0
        return MarketSnapshot(
            symbol=symbol.upper(),
            asset_class=AssetClass.CRYPTO,
            timestamp=int(time.time()),
            price=last_close,
            timeframe=timeframe,
            ohlcv=candles,
            source=self.name,
            status=DataStatus.LIVE,
        )

    # -- internal -------------------------------------------------------

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        # "BTC/USDT" atau "btcusdt" -> "BTCUSDT" (format native Binance)
        return symbol.upper().replace("/", "").replace("-", "").replace("_", "")

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self._base_url}{path}"
        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
        except requests.exceptions.Timeout as exc:
            raise ProviderTimeoutError(
                self.name, str(params.get("symbol", "?")), self._timeout
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ProviderOutageError(self.name, str(exc)) from exc

        if response.status_code == 429 or response.status_code == 418:
            retry_after = response.headers.get("Retry-After")
            raise ProviderRateLimitError(
                self.name,
                retry_after_seconds=float(retry_after) if retry_after else None,
            )
        if response.status_code == 400:
            # Binance mengembalikan 400 dengan code -1121 untuk symbol invalid
            raise InvalidSymbolError(self.name, str(params.get("symbol", "?")))
        if response.status_code >= 500:
            raise ProviderOutageError(
                self.name, f"HTTP {response.status_code}: {response.text[:200]}"
            )
        if response.status_code != 200:
            raise MalformedResponseError(
                self.name, f"Unexpected HTTP {response.status_code}: {response.text[:200]}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise MalformedResponseError(self.name, "Response bukan JSON valid") from exc

    def _parse_ticker(self, symbol: str, raw: Any) -> MarketSnapshot:
        required_fields = (
            "lastPrice",
            "bidPrice",
            "askPrice",
            "volume",
            "priceChangePercent",
        )
        if not isinstance(raw, dict) or not all(f in raw for f in required_fields):
            raise MalformedResponseError(
                self.name, f"Field ticker hilang, dapat keys: {list(raw)[:10] if isinstance(raw, dict) else type(raw)}"
            )
        try:
            price = float(raw["lastPrice"])
            bid = float(raw["bidPrice"])
            ask = float(raw["askPrice"])
            volume = float(raw["volume"])
            pct_change = float(raw["priceChangePercent"])
        except (TypeError, ValueError) as exc:
            raise MalformedResponseError(self.name, f"Gagal parse angka: {exc}") from exc

        return MarketSnapshot(
            symbol=symbol.upper(),
            asset_class=AssetClass.CRYPTO,
            timestamp=int(time.time()),
            price=price,
            timeframe="1D",  # ticker/24hr merepresentasikan window rolling 24 jam
            ohlcv=(),
            source=self.name,
            bid=bid,
            ask=ask,
            volume_24h=volume,
            percentage_change_24h=pct_change,
            status=DataStatus.LIVE,
        )

    def _parse_klines(self, raw: Any) -> tuple[Candle, ...]:
        if not isinstance(raw, list):
            raise MalformedResponseError(
                self.name, f"Response klines bukan list, dapat: {type(raw)}"
            )
        candles: list[Candle] = []
        for i, row in enumerate(raw):
            # Format Binance kline: [openTime, open, high, low, close, volume, ...]
            if not isinstance(row, list) or len(row) < 6:
                raise MalformedResponseError(
                    self.name, f"Baris kline ke-{i} tidak sesuai format (dapat {row!r})"
                )
            try:
                candles.append(
                    Candle(
                        timestamp=int(row[0]) // 1000,  # Binance pakai milliseconds
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[5]),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise MalformedResponseError(
                    self.name, f"Gagal parse candle ke-{i}: {exc}"
                ) from exc
        return tuple(candles)
