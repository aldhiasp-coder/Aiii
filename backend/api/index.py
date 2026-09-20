"""
API layer -- Phase 1 lanjutan (spek poin 4-6).

Ini adalah entrypoint yang dicari Vercel secara otomatis (zero-config
detection untuk FastAPI): instance bernama `app` di `api/index.py`.

Route di sini TIDAK mengarang data. Semuanya memanggil provider dan
indikator asli yang sudah ada di `app/providers` dan `app/indicators`,
lalu memetakan setiap exception ke HTTP status yang sesuai (spek poin 34
-- ERROR HANDLING).
"""

from __future__ import annotations

from typing import Sequence

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.core.exceptions import (
    InsufficientDataError,
    InvalidSymbolError,
    MalformedResponseError,
    MarketDataError,
    ProviderOutageError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    UnsupportedTimeframeError,
)
from app.domain.models import Candle, MarketSnapshot
from app.indicators.momentum import cci, macd, rsi, stochastic
from app.indicators.trend import ema, sma, vwap
from app.indicators.volatility import atr, bollinger_bands
from app.indicators.volume import obv, volume_ma
from app.providers.binance import BinanceProvider

app = FastAPI(title="AI Market Intelligence Terminal -- Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: ganti ke domain frontend asli sebelum production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Provider aktif. Nanti provider lain (forex/gold) tinggal ditambahkan di
# sini tanpa mengubah route -- itulah gunanya abstraction layer ยง4.
_binance = BinanceProvider()


def _error_to_http(exc: MarketDataError) -> HTTPException:
    if isinstance(exc, InvalidSymbolError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, UnsupportedTimeframeError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, ProviderRateLimitError):
        return HTTPException(status_code=429, detail=str(exc))
    if isinstance(exc, ProviderTimeoutError):
        return HTTPException(status_code=504, detail=str(exc))
    if isinstance(exc, (ProviderOutageError, MalformedResponseError)):
        return HTTPException(status_code=502, detail=str(exc))
    if isinstance(exc, InsufficientDataError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "provider": _binance.name}


@app.get("/snapshot/{symbol}")
@app.get("/api/snapshot/{symbol}")
def snapshot(symbol: str) -> MarketSnapshot:
    """Harga terkini (spek poin 4 -- Price)."""
    try:
        return _binance.get_snapshot(symbol)
    except MarketDataError as exc:
        raise _error_to_http(exc) from exc


@app.get("/ohlcv/{symbol}")
@app.get("/api/ohlcv/{symbol}")
def ohlcv(
    symbol: str,
    timeframe: str = Query("1H", description="1m,3m,5m,15m,30m,1H,4H,1D,1W"),
    limit: int = Query(200, ge=1, le=1000),
) -> MarketSnapshot:
    try:
        return _binance.get_ohlcv(symbol, timeframe, limit=limit)
    except MarketDataError as exc:
        raise _error_to_http(exc) from exc


@app.get("/indicators/{symbol}")
@app.get("/api/indicators/{symbol}")
def indicators(
    symbol: str,
    timeframe: str = Query("1H", description="1m,3m,5m,15m,30m,1H,4H,1D,1W"),
    limit: int = Query(200, ge=1, le=1000),
) -> dict:
    """
    Semua indikator teknikal (spek poin 6), dihitung dari OHLCV asli.
    Setiap indikator mengembalikan {value, signal, interpretation,
    timeframe} -- tidak ada angka mentah tanpa interpretasi.
    """
    try:
        snap = _binance.get_ohlcv(symbol, timeframe, limit=limit)
    except MarketDataError as exc:
        raise _error_to_http(exc) from exc

    candles: Sequence[Candle] = snap.ohlcv
    results: dict[str, object] = {}
    computed: list[tuple[str, callable]] = [
        ("sma_20", lambda: sma(candles, 20, timeframe)),
        ("sma_50", lambda: sma(candles, 50, timeframe)),
        ("ema_20", lambda: ema(candles, 20, timeframe)),
        ("ema_50", lambda: ema(candles, 50, timeframe)),
        ("vwap", lambda: vwap(candles, timeframe)),
        ("rsi_14", lambda: rsi(candles, 14, timeframe)),
        ("macd", lambda: macd(candles, timeframe=timeframe)),
        ("stochastic", lambda: stochastic(candles, timeframe=timeframe)),
        ("cci_20", lambda: cci(candles, timeframe=timeframe)),
        ("atr_14", lambda: atr(candles, timeframe=timeframe)),
        ("bollinger", lambda: bollinger_bands(candles, timeframe=timeframe)),
        ("obv", lambda: obv(candles, timeframe=timeframe)),
        ("volume_ma_20", lambda: volume_ma(candles, timeframe=timeframe)),
    ]

    errors: dict[str, str] = {}
    for key, fn in computed:
        try:
            results[key] = fn()
        except InsufficientDataError as exc:
            # Satu indikator kurang data (mis. butuh 200 candle) tidak
            # boleh menjatuhkan seluruh response -- spek poin 34.
            errors[key] = str(exc)

    return {
        "symbol": snap.symbol,
        "timeframe": timeframe,
        "source": snap.source,
        "status": snap.resolved_status().value,
        "candles_used": len(candles),
        "indicators": results,
        "unavailable": errors,
      }
  
