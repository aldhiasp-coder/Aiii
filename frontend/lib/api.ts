import type { IndicatorsResponse, MarketSnapshot } from "./types";

/**
 * SEMUA request market data WAJIB lewat sini -> backend AI Market
 * Intelligence Terminal. Frontend tidak pernah memanggil Binance/Kraken
 * atau exchange lain secara langsung.
 */

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_BACKEND_URL;
  if (!url) {
    throw new ApiError(
      "NEXT_PUBLIC_BACKEND_URL belum di-set. Tambahkan environment variable ini di Vercel Project Settings, lalu redeploy.",
      500
    );
  }
  return url.replace(/\/+$/, "");
}

async function getJson<T>(path: string): Promise<T> {
  const url = `${getBaseUrl()}${path}`;

  let res: Response;
  try {
    res = await fetch(url, { cache: "no-store" });
  } catch {
    throw new ApiError(
      `Tidak bisa menghubungi backend di ${url}. Cek apakah backend sedang online.`,
      0
    );
  }

  if (!res.ok) {
    let detail = res.statusText || `Request gagal (${res.status})`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body?.detail) detail = body.detail;
    } catch {
      // response bukan JSON, pakai statusText apa adanya
    }
    throw new ApiError(detail, res.status);
  }

  return (await res.json()) as T;
}

export function getSnapshot(symbol: string): Promise<MarketSnapshot> {
  return getJson<MarketSnapshot>(`/api/snapshot/${encodeURIComponent(symbol)}`);
}

export function getOhlcv(
  symbol: string,
  timeframe: string,
  limit = 200
): Promise<MarketSnapshot> {
  const params = new URLSearchParams({ timeframe, limit: String(limit) });
  return getJson<MarketSnapshot>(
    `/api/ohlcv/${encodeURIComponent(symbol)}?${params.toString()}`
  );
}

export function getIndicators(
  symbol: string,
  timeframe: string,
  limit = 200
): Promise<IndicatorsResponse> {
  const params = new URLSearchParams({ timeframe, limit: String(limit) });
  return getJson<IndicatorsResponse>(
    `/api/indicators/${encodeURIComponent(symbol)}?${params.toString()}`
  );
}
