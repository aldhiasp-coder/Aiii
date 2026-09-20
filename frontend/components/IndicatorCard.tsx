import type { Signal } from "@/lib/types";

interface IndicatorCardProps {
  title: string;
  valueLabel: string;
  signal?: Signal;
  interpretation?: string;
  unavailableReason?: string;
}

function signalStyle(signal?: Signal): { text: string; classes: string } {
  switch (signal) {
    case "strong_bullish":
    case "bullish_momentum":
    case "bullish":
      return { text: "Bullish", classes: "bg-bull/15 text-bull border-bull/30" };
    case "strong_bearish":
    case "bearish_momentum":
    case "bearish":
      return { text: "Bearish", classes: "bg-bear/15 text-bear border-bear/30" };
    case "overbought":
      return { text: "Overbought", classes: "bg-amber-500/15 text-amber-400 border-amber-500/30" };
    case "oversold":
      return { text: "Oversold", classes: "bg-amber-500/15 text-amber-400 border-amber-500/30" };
    case "expanding":
      return { text: "Expanding", classes: "bg-sky-500/15 text-sky-400 border-sky-500/30" };
    case "contracting":
      return { text: "Contracting", classes: "bg-neutral-500/15 text-neutral-400 border-neutral-500/30" };
    default:
      return { text: "Neutral", classes: "bg-neutral-500/15 text-neutral-400 border-neutral-500/30" };
  }
}

export default function IndicatorCard({
  title,
  valueLabel,
  signal,
  interpretation,
  unavailableReason,
}: IndicatorCardProps) {
  if (unavailableReason) {
    return (
      <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-3">
        <p className="text-xs font-medium text-neutral-500">{title}</p>
        <p className="mt-1 text-xs text-neutral-600">Data belum cukup</p>
      </div>
    );
  }

  const badge = signalStyle(signal);

  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-neutral-400">{title}</p>
        <span className={`rounded border px-1.5 py-0.5 text-[10px] font-medium ${badge.classes}`}>
          {badge.text}
        </span>
      </div>
      <p className="mt-1 text-base font-semibold tabular-nums text-neutral-50">{valueLabel}</p>
      {interpretation && (
        <p className="mt-1 line-clamp-2 text-[11px] leading-snug text-neutral-500">
          {interpretation}
        </p>
      )}
    </div>
  );
}
