"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, getIndicators, getOhlcv, getSnapshot } from "@/lib/api";
import type { IndicatorsResponse, MarketSnapshot } from "@/lib/types";

interface MarketDataState {
  snapshot: MarketSnapshot | null;
  ohlcv: MarketSnapshot | null;
  indicators: IndicatorsResponse | null;
  loading: boolean;
  error: string | null;
}

const POLL_INTERVAL_MS = 20_000;
const OHLCV_LIMIT = 200;

export function useMarketData(symbol: string, timeframe: string) {
  const [state, setState] = useState<MarketDataState>({
    snapshot: null,
    ohlcv: null,
    indicators: null,
    loading: true,
    error: null,
  });

  const load = useCallback(
    async (isBackgroundRefresh: boolean) => {
      if (!isBackgroundRefresh) {
        setState((prev) => ({ ...prev, loading: true, error: null }));
      }
      try {
        const [snapshot, ohlcv, indicators] = await Promise.all([
          getSnapshot(symbol),
          getOhlcv(symbol, timeframe, OHLCV_LIMIT),
          getIndicators(symbol, timeframe, OHLCV_LIMIT),
        ]);
        setState({ snapshot, ohlcv, indicators, loading: false, error: null });
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Terjadi kesalahan tak terduga saat mengambil data.";
        setState((prev) => ({ ...prev, loading: false, error: message }));
      }
    },
    [symbol, timeframe]
  );

  useEffect(() => {
    load(false);
    const intervalId = setInterval(() => load(true), POLL_INTERVAL_MS);
    return () => clearInterval(intervalId);
  }, [load]);

  return { ...state, refresh: () => load(false) };
}
