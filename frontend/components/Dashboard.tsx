"use client";

import { useState } from "react";
import { useMarketData } from "@/hooks/useMarketData";
import { SYMBOLS, TIMEFRAMES, type SymbolTicker, type Timeframe } from "@/lib/types";
import Header from "./Header";
import SymbolSelector from "./SymbolSelector";
import TimeframeSelector from "./TimeframeSelector";
import MarketChart from "./MarketChart";
import IndicatorPanel from "./IndicatorPanel";
import AnalysisPanel from "./AnalysisPanel";
import LoadingState from "./LoadingState";
import ErrorState from "./ErrorState";

export default function Dashboard() {
  const [symbol, setSymbol] = useState<SymbolTicker>("BTCUSDT");
  const [timeframe, setTimeframe] = useState<Timeframe>("1H");

  const { snapshot, ohlcv, indicators, loading, error, refresh } = useMarketData(
    symbol,
    timeframe
  );

  const hasInitialData = Boolean(ohlcv && indicators);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <Header snapshot={snapshot} symbol={symbol} loading={loading} />

      <main className="mx-auto max-w-6xl space-y-4 px-4 py-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <SymbolSelector symbols={SYMBOLS} active={symbol} onChange={setSymbol} />
          <TimeframeSelector timeframes={TIMEFRAMES} active={timeframe} onChange={setTimeframe} />
        </div>

        {error && <ErrorState message={error} onRetry={refresh} />}

        {!error && !hasInitialData && loading && <LoadingState />}

        {!error && ohlcv && (
          <section className="rounded-xl border border-neutral-800 bg-neutral-900 p-2 sm:p-3">
            <MarketChart candles={ohlcv.ohlcv} />
          </section>
        )}

        {!error && indicators && (
          <>
            <IndicatorPanel data={indicators} />
            <AnalysisPanel data={indicators} />
          </>
        )}
      </main>
    </div>
  );
}
