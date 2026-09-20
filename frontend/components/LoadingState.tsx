export default function LoadingState() {
  return (
    <div className="space-y-3" role="status" aria-live="polite">
      <div className="h-[380px] animate-pulse rounded-xl border border-neutral-800 bg-neutral-900" />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 7 }).map((_, idx) => (
          <div
            key={idx}
            className="h-20 animate-pulse rounded-lg border border-neutral-800 bg-neutral-900"
          />
        ))}
      </div>
      <span className="sr-only">Memuat data market...</span>
    </div>
  );
}
