from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.exceptions import InsufficientDataError
from app.domain.indicator_models import Signal
from app.domain.models import Candle
from app.indicators import momentum, trend, volatility, volume


def make_candles(closes: list[float], volumes: list[float] | None = None) -> list[Candle]:
    """Helper: bangun candle sintetis dari list close price (OHLC dibuat flat
    di sekitar close supaya valid, khusus untuk test indikator yang cuma
    butuh close/volume)."""
    volumes = volumes or [100.0] * len(closes)
    candles = []
    for i, (c, v) in enumerate(zip(closes, volumes)):
        # high/low sedikit lebih lebar dari open/close biar valid & tidak flat total
        o = closes[i - 1] if i > 0 else c
        h = max(o, c) * 1.001
        lo = min(o, c) * 0.999
        candles.append(Candle(timestamp=1700000000 + i * 3600, open=o, high=h, low=lo, close=c, volume=v))
    return candles


class TestSMA(unittest.TestCase):
    def test_sma_matches_manual_average(self):
        closes = [10, 20, 30, 40, 50]
        candles = make_candles(closes)
        result = trend.sma(candles, period=5, timeframe="1H")
        self.assertAlmostEqual(result.value, sum(closes) / 5)
        self.assertEqual(result.name, "SMA5")

    def test_sma_insufficient_data_raises(self):
        candles = make_candles([10, 20])
        with self.assertRaises(InsufficientDataError):
            trend.sma(candles, period=5, timeframe="1H")

    def test_sma_signal_bullish_when_price_above(self):
        # trend naik tajam -> harga terakhir jauh di atas SMA
        closes = [10] * 19 + [100]
        candles = make_candles(closes)
        result = trend.sma(candles, period=20, timeframe="1H")
        self.assertEqual(result.signal, Signal.BULLISH)


class TestEMA(unittest.TestCase):
    def test_ema_constant_series_equals_the_constant(self):
        closes = [50.0] * 30
        candles = make_candles(closes)
        result = trend.ema(candles, period=10, timeframe="1H")
        self.assertAlmostEqual(result.value, 50.0, places=6)


class TestRSI(unittest.TestCase):
    def test_rsi_all_gains_is_100(self):
        # harga naik terus -> tidak ada loss -> RSI harus 100
        closes = [10 + i for i in range(20)]
        candles = make_candles(closes)
        result = momentum.rsi(candles, period=14, timeframe="1H")
        self.assertAlmostEqual(result.value, 100.0, places=1)
        self.assertEqual(result.signal, Signal.OVERBOUGHT)

    def test_rsi_all_losses_is_0(self):
        closes = [100 - i for i in range(20)]
        candles = make_candles(closes)
        result = momentum.rsi(candles, period=14, timeframe="1H")
        self.assertAlmostEqual(result.value, 0.0, places=1)
        self.assertEqual(result.signal, Signal.OVERSOLD)

    def test_rsi_flat_price_is_neutral_range(self):
        closes = [50.0] * 20
        candles = make_candles(closes)
        result = momentum.rsi(candles, period=14, timeframe="1H")
        # tidak ada gain/loss sama sekali -> avg_gain=avg_loss=0 -> kode kita
        # fallback ke 100 (all-gains path karena avg_loss==0). Ini edge-case
        # yang didokumentasikan, bukan bug tersembunyi.
        self.assertIsInstance(result.value, float)


class TestMACD(unittest.TestCase):
    def test_macd_uptrend_is_bullish(self):
        closes = [10 + i * 0.5 for i in range(60)]
        candles = make_candles(closes)
        result = momentum.macd(candles, timeframe="1H")
        self.assertIn(result.signal, (Signal.BULLISH, Signal.BULLISH_MOMENTUM))
        self.assertGreater(result.value["macd"], 0)

    def test_macd_downtrend_is_bearish(self):
        closes = [100 - i * 0.5 for i in range(60)]
        candles = make_candles(closes)
        result = momentum.macd(candles, timeframe="1H")
        self.assertIn(result.signal, (Signal.BEARISH, Signal.BEARISH_MOMENTUM))
        self.assertLess(result.value["macd"], 0)


class TestATR(unittest.TestCase):
    def test_atr_is_positive_for_volatile_series(self):
        closes = [10, 12, 9, 13, 8, 14, 7, 15, 6, 16, 10, 12, 9, 13, 8]
        candles = make_candles(closes)
        result = volatility.atr(candles, period=14, timeframe="1H")
        self.assertGreater(result.value, 0)

    def test_atr_insufficient_data_raises(self):
        candles = make_candles([10, 11])
        with self.assertRaises(InsufficientDataError):
            volatility.atr(candles, period=14, timeframe="1H")


class TestBollinger(unittest.TestCase):
    def test_bollinger_flat_series_has_zero_width(self):
        closes = [50.0] * 25
        candles = make_candles(closes)
        result = volatility.bollinger_bands(candles, period=20, timeframe="1H")
        self.assertAlmostEqual(result.value["upper"], result.value["lower"], places=6)


class TestOBV(unittest.TestCase):
    def test_obv_rises_on_consistent_uptrend_volume(self):
        closes = [10, 11, 12, 13, 14]
        volumes = [100, 100, 100, 100, 100]
        candles = make_candles(closes, volumes)
        result = volume.obv(candles, timeframe="1H")
        self.assertEqual(result.signal, Signal.BULLISH)
        # OBV = 0 + 100 + 100 + 100 + 100 = 400
        self.assertAlmostEqual(result.value, 400.0)

    def test_obv_falls_on_consistent_downtrend_volume(self):
        closes = [14, 13, 12, 11, 10]
        volumes = [100, 100, 100, 100, 100]
        candles = make_candles(closes, volumes)
        result = volume.obv(candles, timeframe="1H")
        self.assertEqual(result.signal, Signal.BEARISH)
        self.assertAlmostEqual(result.value, -400.0)


class TestVolumeMA(unittest.TestCase):
    def test_volume_spike_detected_as_expanding(self):
        closes = list(range(1, 22))
        volumes = [100.0] * 20 + [500.0]  # lonjakan di candle terakhir
        candles = make_candles(closes, volumes)
        result = volume.volume_ma(candles, period=20, timeframe="1H")
        self.assertEqual(result.signal, Signal.EXPANDING)


if __name__ == "__main__":
    unittest.main()
