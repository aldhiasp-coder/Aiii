"""
MarketDataProvider abstraction (spek poin 4).

Setiap provider (Binance, TwelveData, OANDA, dst) mengimplementasikan
interface ini. Layer di atasnya (normalizer, indicator engine, API) HANYA
bergantung pada interface ini -- tidak pernah pada detail provider tertentu.
Ini yang membuat provider bisa diganti tanpa mengubah seluruh aplikasi.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models import AssetClass, MarketSnapshot


class MarketDataProvider(ABC):
    """Kontrak yang wajib dipenuhi setiap integrasi data market."""

    #: Nama provider untuk logging/error/atribusi ("Source: Binance" di UI)
    name: str

    #: Timeframe yang BENAR-BENAR didukung provider secara native.
    #: Provider TIDAK BOLEH mengklaim mendukung timeframe di luar ini
    #: tanpa strategi derive yang eksplisit (lihat `derive_timeframes`).
    supported_timeframes: frozenset[str]

    #: Asset class yang dilayani provider ini.
    asset_classes: frozenset[AssetClass]

    @abstractmethod
    def get_snapshot(self, symbol: str) -> MarketSnapshot:
        """
        Ambil snapshot harga terkini (tanpa OHLCV historis, ohlcv=() kosong
        atau berisi 1 candle terakhir tergantung provider) untuk `symbol`.

        Raises:
            InvalidSymbolError, ProviderTimeoutError, ProviderRateLimitError,
            ProviderOutageError, MalformedResponseError
        """
        raise NotImplementedError

    @abstractmethod
    def get_ohlcv(
        self, symbol: str, timeframe: str, limit: int = 200
    ) -> MarketSnapshot:
        """
        Ambil `limit` candle terakhir untuk `symbol` pada `timeframe`.

        Jika `timeframe` tidak ada di `supported_timeframes`, implementasi
        HARUS raise `UnsupportedTimeframeError` -- caller (bukan provider)
        yang memutuskan apakah akan derive dari lower timeframe atau
        menampilkan "unavailable" (lihat `derive_timeframes.py`).
        """
        raise NotImplementedError

    def supports(self, asset_class: AssetClass, timeframe: str) -> bool:
        return asset_class in self.asset_classes and timeframe in self.supported_timeframes
