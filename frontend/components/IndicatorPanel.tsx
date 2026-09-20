import type { IndicatorsResponse } from "@/lib/types";
import { formatPrice } from "@/lib/format";
import IndicatorCard from "./IndicatorCard";

interface IndicatorPanelProps {
  data: IndicatorsResponse;
}

export default function IndicatorPanel({ data }: IndicatorPanelProps) {
  const { sma_20, sma_50, ema_20, ema_50, vwap, rsi_14, macd } = data.indicators;
  const unavailable = data.unavailable ?? {};

  return (
    <section>
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
        Indicators -- {data.timeframe}
      </h2>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        <IndicatorCard
          title="SMA 20"
          valueLabel={sma_20 ? formatPrice(sma_20.value) : "--"}
          signal={sma_20?.signal}
          interpretation={sma_20?.interpretation}
          unavailableReason={unavailable.sma_20}
        />
        <IndicatorCard
          title="SMA 50"
          valueLabel={sma_50 ? formatPrice(sma_50.value) : "--"}
          signal={sma_50?.signal}
          interpretation={sma_50?.interpretation}
          unavailableReason={unavailable.sma_50}
        />
        <IndicatorCard
          title="EMA 20"
          valueLabel={ema_20 ? formatPrice(ema_20.value) : "--"}
          signal={ema_20?.signal}
          interpretation={ema_20?.interpretation}
          unavailableReason={unavailable.ema_20}
        />
        <IndicatorCard
          title="EMA 50"
          valueLabel={ema_50 ? formatPrice(ema_50.value) : "--"}
          signal={ema_50?.signal}
          interpretation={ema_50?.interpretation}
          unavailableReason={unavailable.ema_50}
        />
        <IndicatorCard
          title="VWAP"
          valueLabel={vwap ? formatPrice(vwap.value) : "--"}
          signal={vwap?.signal}
          interpretation={vwap?.interpretation}
          unavailableReason={unavailable.vwap}
        />
        <IndicatorCard
          title="RSI 14"
          valueLabel={rsi_14 ? rsi_14.value.toFixed(1) : "--"}
          signal={rsi_14?.signal}
          interpretation={rsi_14?.interpretation}
          unavailableReason={unavailable.rsi_14}
        />
        <IndicatorCard
          title="MACD"
          valueLabel={
            macd
              ? `${macd.value.macd.toFixed(4)} / ${macd.value.signal.toFixed(4)}`
              : "--"
          }
          signal={macd?.signal}
          interpretation={macd?.interpretation}
          unavailableReason={unavailable.macd}
        />
      </div>
    </section>
  );
}
