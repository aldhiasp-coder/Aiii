"""
Test BinanceProvider tanpa network sungguhan: `requests.Session.get` di-mock
agar mengembalikan fixture sample yang formatnya sesuai dokumentasi resmi
Binance API. Ini membuktikan parsing & normalisasi logic-nya benar, meski
tidak bisa membuktikan endpoint aslinya bisa dihubungi dari sandbox ini
(karena network egress dimatikan).
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.exceptions import (
    InvalidSymbolError,
    MalformedResponseError,
    ProviderOutageError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    UnsupportedTimeframeError,
)
from app.domain.models import AssetClass, DataStatus
from app.providers.binance import BinanceProvider

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _load_fixture(name: str):
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


def _mock_response(status_code: int, json_body, headers: dict | None = None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body
    resp.text = json.dumps(json_body) if not isinstance(json_body, str) else json_body
    resp.headers = headers or {}
    return resp


class TestBinanceProviderOHLCV(unittest.TestCase):
    def setUp(self) -> None:
        self.session = MagicMock()
        self.provider = BinanceProvider(session=self.session)
        self.klines = _load_fixture("binance_klines_sample.json")

    def test_parses_klines_into_normalized_candles(self):
        self.session.get.return_value = _mock_response(200, self.klines)

        snapshot = self.provider.get_ohlcv("BTC/USDT", "1H", limit=5)

        self.assertEqual(snapshot.symbol, "BTC/USDT")
        self.assertEqual(snapshot.asset_class, AssetClass.CRYPTO)
        self.assertEqual(snapshot.source, "Binance")
        self.assertEqual(len(snapshot.ohlcv), 5)

        first = snapshot.ohlcv[0]
        self.assertEqual(first.timestamp, 1700000000000 // 1000)
        self.assertAlmostEqual(first.open, 36500.10)
        self.assertAlmostEqual(first.high, 36620.50)
        self.assertAlmostEqual(first.low, 36480.00)
        self.assertAlmostEqual(first.close, 36590.20)
        self.assertAlmostEqual(first.volume, 1234.567)

        # snapshot.price harus sama dengan close candle terakhir
        self.assertAlmostEqual(snapshot.price, snapshot.ohlcv[-1].close)

        # candle harus urut naik berdasarkan waktu
        timestamps = [c.timestamp for c in snapshot.ohlcv]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_symbol_is_normalized_to_binance_format_in_request(self):
        self.session.get.return_value = _mock_response(200, self.klines)
        self.provider.get_ohlcv("btc-usdt", "1H")
        called_params = self.session.get.call_args.kwargs["params"]
        self.assertEqual(called_params["symbol"], "BTCUSDT")
        self.assertEqual(called_params["interval"], "1h")

    def test_unsupported_timeframe_raises_before_any_request(self):
        with self.assertRaises(UnsupportedTimeframeError):
            self.provider.get_ohlcv("BTCUSDT", "2H")  # Binance spot tidak native 2H
        self.session.get.assert_not_called()

    def test_rate_limit_maps_to_provider_rate_limit_error(self):
        self.session.get.return_value = _mock_response(
            429, {"code": -1003, "msg": "Too many requests"}, headers={"Retry-After": "2"}
        )
        with self.assertRaises(ProviderRateLimitError) as ctx:
            self.provider.get_ohlcv("BTCUSDT", "1H")
        self.assertEqual(ctx.exception.retry_after_seconds, 2.0)

    def test_invalid_symbol_maps_to_invalid_symbol_error(self):
        self.session.get.return_value = _mock_response(
            400, {"code": -1121, "msg": "Invalid symbol."}
        )
        with self.assertRaises(InvalidSymbolError):
            self.provider.get_ohlcv("NOTREAL", "1H")

    def test_server_error_maps_to_provider_outage_error(self):
        self.session.get.return_value = _mock_response(503, "Service Unavailable")
        with self.assertRaises(ProviderOutageError):
            self.provider.get_ohlcv("BTCUSDT", "1H")

    def test_timeout_maps_to_provider_timeout_error(self):
        import requests

        self.session.get.side_effect = requests.exceptions.Timeout()
        with self.assertRaises(ProviderTimeoutError):
            self.provider.get_ohlcv("BTCUSDT", "1H")

    def test_malformed_kline_row_raises_malformed_response_error(self):
        broken = [[1700000000000, "36500.10", "36620.50"]]  # kurang field
        self.session.get.return_value = _mock_response(200, broken)
        with self.assertRaises(MalformedResponseError):
            self.provider.get_ohlcv("BTCUSDT", "1H")

    def test_non_list_response_raises_malformed_response_error(self):
        self.session.get.return_value = _mock_response(200, {"unexpected": "shape"})
        with self.assertRaises(MalformedResponseError):
            self.provider.get_ohlcv("BTCUSDT", "1H")


class TestBinanceProviderTicker(unittest.TestCase):
    def setUp(self) -> None:
        self.session = MagicMock()
        self.provider = BinanceProvider(session=self.session)
        self.ticker = _load_fixture("binance_ticker_sample.json")

    def test_parses_ticker_snapshot(self):
        self.session.get.return_value = _mock_response(200, self.ticker)

        snapshot = self.provider.get_snapshot("BTCUSDT")

        self.assertAlmostEqual(snapshot.price, 36650.00)
        self.assertAlmostEqual(snapshot.bid, 36649.50)
        self.assertAlmostEqual(snapshot.ask, 36650.50)
        self.assertAlmostEqual(snapshot.volume_24h, 18234.567)
        self.assertAlmostEqual(snapshot.percentage_change_24h, 0.412)
        self.assertEqual(snapshot.status, DataStatus.LIVE)
        self.assertIsNotNone(snapshot.spread)
        self.assertAlmostEqual(snapshot.spread, 1.0, places=2)

    def test_missing_required_field_raises_malformed_response_error(self):
        broken_ticker = dict(self.ticker)
        del broken_ticker["bidPrice"]
        self.session.get.return_value = _mock_response(200, broken_ticker)
        with self.assertRaises(MalformedResponseError):
            self.provider.get_snapshot("BTCUSDT")


if __name__ == "__main__":
    unittest.main()
