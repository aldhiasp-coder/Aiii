import type { MarketSnapshot } from "@/lib/types";
import { formatPercent, formatPrice } from "@/lib/format";

interface HeaderProps {
  snapshot: MarketSnapshot | null;
  symbol: string;
  loading: boolean;
}

export default function Header({ snapshot, symbol, loading }: HeaderProps) {
  const change = snapshot?.percentage_change_24h ?? null;
  const changeColor =
    change === null ? "text-neutral-400" : change >= 0 ? "text-bull" : "text-bear";

  const status = snapshot?.status ?? (loading ? null : "UNAVAILABLE");
  const statusColor =
    status === "LIVE" ? "bg-bull" : status === "STALE" ? "bg-amber-500" : "bg-neutral-600";

  return (
    <header className="sticky top-0 z-10 border-b border-neutral-800 bg-neutral-950/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 py-3">
        <div className="flex items-center gap-2">
          <h1 className="text-sm font-semibold tracking-wide text-neutral-100 sm:text-base">
            AI Market Intelligence
          </h1>
          <span className="flex items-center gap-1.5 rounded-full border border-neutral-800 px-2 py-0.5 text-[11px] font-medium text-neutral-300">
            <span className={`h-1.5 w-1.5 rounded-full ${statusColor} animate-pulse`} />
            {status ?? "..."}
          </span>
        </div>

        <div className="flex items-baseline gap-3">
          <span className="text-sm font-medium text-neutral-400">{symbol}</span>
          <span className="text-lg font-semibold tabular-nums text-neutral-50 sm:text-xl">
            {snapshot ? formatPrice(snapshot.price) : "--"}
          </span>
          <span className={`text-sm font-medium tabular-nums ${changeColor}`}>
            {formatPercent(change)}
          </span>
        </div>
      </div>
    </header>
  );
}
