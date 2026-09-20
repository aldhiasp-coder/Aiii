interface TimeframeSelectorProps<T extends string> {
  timeframes: readonly T[];
  active: T;
  onChange: (timeframe: T) => void;
}

export default function TimeframeSelector<T extends string>({
  timeframes,
  active,
  onChange,
}: TimeframeSelectorProps<T>) {
  return (
    <div className="flex gap-1.5 overflow-x-auto rounded-lg border border-neutral-800 bg-neutral-900 p-1">
      {timeframes.map((tf) => (
        <button
          key={tf}
          type="button"
          onClick={() => onChange(tf)}
          aria-pressed={tf === active}
          className={`whitespace-nowrap rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors sm:text-sm ${
            tf === active
              ? "bg-neutral-100 text-neutral-900"
              : "text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200"
          }`}
        >
          {tf}
        </button>
      ))}
    </div>
  );
}
