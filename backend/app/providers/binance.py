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


BASE_URL = "https://api.kraken.com"


_INTERVAL_MAP: dict[str, int] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1H": 60,
    "4H": 240,
    "1D": 1440,
    "1W": 10080,
}


class BinanceProvider(MarketDataProvider):
    """
    Compatibility provider.

    Nama class tetap BinanceProvider supaya api/index.py tidak perlu
    diubah, tetapi sumber data sekarang menggunakan Kraken Public API.
    """

    name = "Kraken"
    supported_timeframes = frozenset(_INTERVAL_MAP.keys())
    asset_classes = frozenset({AssetClass.CRYPTO})

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout_seconds: float = 10.0,
        base_url: str = BASE_URL,
    ) -> None:
        self._session = session or requests.Session()
        self._timeout = timeout_seconds
        self._base_url = base_url

    def get_snapshot(self, symbol: str) -> MarketSnapshot:
        pair = self._normalize_symbol(symbol)

        raw = self._request(
            "/0/public/Ticker",
            params={"pair": pair},
        )

        if not isinstance(raw, dict):
            raise MalformedResponseError(
                self.name,
                "Response ticker bukan object",
            )

        result = raw.get("result")

        if not isinstance(result, dict) or not result:
            raise InvalidSymbolError(self.name, symbol)

        ticker = next(iter(result.values()))

        if not isinstance(ticker, dict):
            raise MalformedResponseError(
                self.name,
                "Data ticker tidak sesuai schema",
            )

        try:
            price = float(ticker["c"][0])
            bid = float(ticker["b"][0])
            ask = float(ticker["a"][0])
            volume = float(ticker["v"][1])

            open_price = float(ticker["o"])

            if open_price != 0:
                pct_change = ((price - open_price) / open_price) * 100
            else:
                pct_change = 0.0

        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise MalformedResponseError(
                self.name,
                f"Gagal parse ticker: {exc}",
            ) from exc

        return MarketSnapshot(
            symbol=symbol.upper(),
            asset_class=AssetClass.CRYPTO,
            timestamp=int(time.time()),
            price=price,
            timeframe="1D",
            ohlcv=(),
            source=self.name,
            bid=bid,
            ask=ask,
            volume_24h=volume,
            percentage_change_24h=pct_change,
            status=DataStatus.LIVE,
        )

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 200,
    ) -> MarketSnapshot:

        if timeframe not in _INTERVAL_MAP:
            raise UnsupportedTimeframeError(self.name, timeframe)

        if not (1 <= limit <= 720):
            raise ValueError("limit harus di antara 1 dan 720")

        interval = _INTERVAL_MAP[timeframe]
        pair = self._normalize_symbol(symbol)

        raw = self._request(
            "/0/public/OHLC",
            params={
                "pair": pair,
                "interval": interval,
            },
        )

        if not isinstance(raw, dict):
            raise MalformedResponseError(
                self.name,
                "Response OHLC bukan object",
            )

        result = raw.get("result")

        if not isinstance(result, dict):
            raise MalformedResponseError(
                self.name,
                "Field result OHLC tidak ditemukan",
            )

        rows = None

        for key, value in result.items():
            if key != "last":
                rows = value
                break

        if not isinstance(rows, list):
            raise MalformedResponseError(
                self.name,
                "Data OHLC tidak ditemukan",
            )

        candles = self._parse_ohlc(rows)

        if not candles:
            raise MalformedResponseError(
                self.name,
                "Kraken mengembalikan candle kosong",
            )

        # Kraken dapat mengembalikan hingga 720 candle.
        # Ambil candle terakhir sesuai limit yang diminta.
        candles = candles[-limit:]

        last_close = candles[-1].close

        return MarketSnapshot(
            symbol=symbol.upper(),
            asset_class=AssetClass.CRYPTO,
            timestamp=int(time.time()),
            price=last_close,
            timeframe=timeframe,
            ohlcv=tuple(candles),
            source=self.name,
            status=DataStatus.LIVE,
        )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """
        BTC/USDT -> XBTUSDT
        BTC/USD  -> XBTUSD

        Kraken menggunakan XBT sebagai simbol Bitcoin pada sebagian
        endpoint REST-nya.
        """

        value = (
            symbol.upper()
            .replace("/", "")
            .replace("-", "")
            .replace("_", "")
        )

        if value.startswith("BTC"):
            value = "XBT" + value[3:]

        return value

    def _request(
        self,
        path: str,
        params: dict[str, Any],
    ) -> Any:

        url = f"{self._base_url}{path}"

        try:
            response = self._session.get(
                url,
                params=params,
                timeout=self._timeout,
            )

        except requests.exceptions.Timeout as exc:
            raise ProviderTimeoutError(
                self.name,
                str(params.get("pair", "?")),
                self._timeout,
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise ProviderOutageError(
                self.name,
                str(exc),
            ) from exc

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")

            raise ProviderRateLimitError(
                self.name,
                retry_after_seconds=(
                    float(retry_after)
                    if retry_after
                    else None
                ),
            )

        if response.status_code >= 500:
            raise ProviderOutageError(
                self.name,
                f"HTTP {response.status_code}: {response.text[:200]}",
            )

        if response.status_code != 200:
            raise MalformedResponseError(
                self.name,
                f"Unexpected HTTP {response.status_code}: "
                f"{response.text[:200]}",
            )

        try:
            data = response.json()

        except ValueError as exc:
            raise MalformedResponseError(
                self.name,
                "Response bukan JSON valid",
            ) from exc

        if not isinstance(data, dict):
            raise MalformedResponseError(
                self.name,
                "Response JSON bukan object",
            )

        errors = data.get("error")

        if errors:
            message = "; ".join(str(error) for error in errors)

            raise MalformedResponseError(
                self.name,
                message,
            )

        return data

    def _parse_ohlc(
        self,
        raw: Any,
    ) -> list[Candle]:

        if not isinstance(raw, list):
            raise MalformedResponseError(
                self.name,
                "Response OHLC bukan list",
            )

        candles: list[Candle] = []

        for i, row in enumerate(raw):

            if not isinstance(row, list) or len(row) < 7:
                raise MalformedResponseError(
                    self.name,
                    f"Baris OHLC ke-{i} tidak sesuai format",
                )

            try:
                candles.append(
                    Candle(
                        timestamp=int(float(row[0])),
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[6]),
                    )
                )

            except (TypeError, ValueError, IndexError) as exc:
                raise MalformedResponseError(
                    self.name,
                    f"Gagal parse candle ke-{i}: {exc}",
                ) from exc

        return candles
