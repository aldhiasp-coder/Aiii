/**
 * Type-type ini disalin 1:1 dari schema backend
 * (app/domain/models.py & app/domain/indicator_models.py) supaya frontend
 * tidak pernah menebak bentuk response -- lihat backend/api/index.py.
 */

export type AssetClass = "crypto" | "forex" | "commodity";

export type DataStatus = "LIVE" | "STALE" | "UNAVAILABLE";

export interface Candle {
  timestamp: number; // unix epoch detik (waktu open candle, UTC)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketSnapshot {
  symbol: string;
  asset_class: AssetClass;
  timestamp: number;
  price: number;
  timeframe: string;
  ohlcv: Candle[];
  source: string;
  bid?: number | null;
  ask?: number | null;
  volume_24h?: number | null;
  percentage_change_24h?: number | null;
  status: DataStatus;
  fetched_at: string;
}

export type Signal =
  | "strong_bullish"
  | "bullish_momentum"
  | "bullish"
  | "neutral"
  | "bearish"
  | "bearish_momentum"
  | "strong_bearish"
  | "overbought"
  | "oversold"
  | "expanding"
  | "contracting";

export interface IndicatorResult<TValue = number> {
  name: string;
  value: TValue;
  signal: Signal;
  interpretation: string;
  timeframe: string;
  series?: number[] | null;
}

export interface MacdValue {
  macd: number;
  signal: number;
  histogram: number;
}

export interface StochasticValue {
  k: number;
  d: number;
}

export interface BollingerValue {
  upper: number;
  middle: number;
  lower: number;
}

export interface IndicatorSet {
  sma_20?: IndicatorResult<number>;
  sma_50?: IndicatorResult<number>;
  ema_20?: IndicatorResult<number>;
  ema_50?: IndicatorResult<number>;
  vwap?: IndicatorResult<number>;
  rsi_14?: IndicatorResult<number>;
  macd?: IndicatorResult<MacdValue>;
  stochastic?: IndicatorResult<StochasticValue>;
  cci_20?: IndicatorResult<number>;
  atr_14?: IndicatorResult<number>;
  bollinger?: IndicatorResult<BollingerValue>;
  obv?: IndicatorResult<number>;
  volume_ma_20?: IndicatorResult<number>;
}

export interface IndicatorsResponse {
  symbol: string;
  timeframe: string;
  source: string;
  status: DataStatus;
  candles_used: number;
  indicators: IndicatorSet;
  unavailable: Record<string, string>;
}

export const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"] as const;
export type SymbolTicker = (typeof SYMBOLS)[number];

export const TIMEFRAMES = ["1m", "5m", "15m", "1H", "4H", "1D"] as const;
export type Timeframe = (typeof TIMEFRAMES)[number];
