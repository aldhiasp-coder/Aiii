import type { IndicatorResult, IndicatorsResponse, Signal } from "./types";

export type Bias = "Bullish" | "Bearish" | "Neutral" | "Mixed";

export interface AnalysisSection {
  label: string;
  bias: Bias;
  reasons: string[];
}

export interface VolatilitySection {
  label: string;
  state: string;
  reasons: string[];
}

function isBullish(signal?: Signal): boolean {
  return signal === "bullish" || signal === "bullish_momentum" || signal === "strong_bullish";
}

function isBearish(signal?: Signal): boolean {
  return signal === "bearish" || signal === "bearish_momentum" || signal === "strong_bearish";
}

// Value shape differs per indicator (number, MacdValue, BollingerValue, ...),
// but here we only ever read `.signal` / `.interpretation`, so the value
// type is intentionally loosened rather than forced to unify.
function pick(...results: (IndicatorResult<any> | undefined)[]): IndicatorResult<any>[] {
  return results.filter((r): r is IndicatorResult<any> => Boolean(r));
}

function biasFromSignals(signals: Signal[]): Bias {
  const bullishCount = signals.filter(isBullish).length;
  const bearishCount = signals.filter(isBearish).length;
  if (bullishCount === 0 && bearishCount === 0) return "Neutral";
  if (bullishCount > bearishCount) return "Bullish";
  if (bearishCount > bullishCount) return "Bearish";
  return "Mixed";
}

/** Trend: SMA20/50, EMA20/50, VWAP -- semuanya trend-following indicators. */
export function buildTrendAnalysis(data: IndicatorsResponse): AnalysisSection {
  const { sma_20, sma_50, ema_20, ema_50, vwap } = data.indicators;
  const items = pick(sma_20, sma_50, ema_20, ema_50, vwap);
  return {
    label: "Trend",
    bias: biasFromSignals(items.map((i) => i.signal)),
    reasons: items.map((i) => i.interpretation),
  };
}

/** Momentum: RSI, MACD, Stochastic, CCI. */
export function buildMomentumAnalysis(data: IndicatorsResponse): AnalysisSection {
  const { rsi_14, macd, stochastic, cci_20 } = data.indicators;
  const items = pick(rsi_14, macd, stochastic, cci_20);
  return {
    label: "Momentum",
    bias: biasFromSignals(items.map((i) => i.signal)),
    reasons: items.map((i) => i.interpretation),
  };
}

/** Volatility: ATR + Bollinger Bands -- bukan bias arah, tapi kondisi pergerakan. */
export function buildVolatilityAnalysis(data: IndicatorsResponse): VolatilitySection {
  const { atr_14, bollinger } = data.indicators;
  const items = pick(atr_14, bollinger);

  let state = "Normal";
  if (atr_14?.signal === "expanding") state = "Melebar (Expanding)";
  else if (atr_14?.signal === "contracting") state = "Menyempit (Contracting)";
  if (bollinger?.signal === "overbought" || bollinger?.signal === "oversold") {
    state = "Ekstrem -- harga menyentuh Bollinger Band";
  }

  return {
    label: "Volatility",
    state,
    reasons: items.map((i) => i.interpretation),
  };
}

/**
 * Ringkasan gabungan. Sengaja tidak menghasilkan skor confidence atau
 * sinyal BUY/SELL -- ini bukan trading signal, hanya rangkuman kondisi
 * teknikal berdasarkan indikator yang benar-benar tersedia.
 */
export function buildSummary(data: IndicatorsResponse): string {
  const trend = buildTrendAnalysis(data);
  const momentum = buildMomentumAnalysis(data);
  const volatility = buildVolatilityAnalysis(data);

  const missing = Object.keys(data.unavailable ?? {});
  const missingNote =
    missing.length > 0
      ? ` Catatan: ${missing.join(", ")} belum bisa dihitung karena data historis belum cukup.`
      : "";

  return (
    `${data.symbol} (${data.timeframe}): trend ${trend.bias.toLowerCase()}, ` +
    `momentum ${momentum.bias.toLowerCase()}, volatilitas ${volatility.state.toLowerCase()}. ` +
    `Dihitung dari ${data.candles_used} candle via ${data.source}.${missingNote}`
  );
}
