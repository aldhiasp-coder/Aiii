interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-3 rounded-xl border border-bear/30 bg-bear/10 p-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <p className="text-sm font-medium text-bear">Gagal memuat data market</p>
        <p className="mt-1 text-xs text-neutral-400">{message}</p>
      </div>
      <button
        type="button"
        onClick={onRetry}
        className="shrink-0 rounded-md border border-bear/40 bg-neutral-950 px-3 py-1.5 text-xs font-medium text-neutral-200 hover:bg-neutral-900"
      >
        Coba lagi
      </button>
    </div>
  );
}
