interface SymbolSelectorProps<T extends string> {
  symbols: readonly T[];
  active: T;
  onChange: (symbol: T) => void;
}

export default function SymbolSelector<T extends string>({
  symbols,
  active,
  onChange,
}: SymbolSelectorProps<T>) {
  return (
    <div className="flex gap-1.5 overflow-x-auto rounded-lg border border-neutral-800 bg-neutral-900 p-1">
      {symbols.map((symbol) => (
        <button
          key={symbol}
          type="button"
          onClick={() => onChange(symbol)}
          aria-pressed={symbol === active}
          className={`whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium transition-colors sm:text-sm ${
            symbol === active
              ? "bg-neutral-100 text-neutral-900"
              : "text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200"
          }`}
        >
          {symbol}
        </button>
      ))}
    </div>
  );
}
