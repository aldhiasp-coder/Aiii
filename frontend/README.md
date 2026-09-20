# AI Market Intelligence Terminal -- Frontend

Next.js (App Router) + TypeScript + Tailwind CSS. Semua data market diambil
dari backend (`aiii-five.vercel.app`), tidak pernah langsung ke exchange.

## Development lokal

```bash
cp .env.example .env.local
# edit .env.local jika backend-mu punya URL berbeda
npm install
npm run dev
```

## Deploy ke Vercel

1. Push folder ini ke repo GitHub `Aiii` (sudah ada backend di `backend/`,
   frontend ini masuk ke folder `frontend/`).
2. Buat **Vercel Project baru** dari repo yang sama (satu repo bisa punya
   dua Vercel Project: satu untuk `backend`, satu untuk `frontend`).
3. **Root Directory** -> pilih **`frontend`**.
4. **Framework Preset** -> biarkan otomatis terdeteksi sebagai **Next.js**.
5. **Environment Variables** -> tambahkan:
   - `NEXT_PUBLIC_BACKEND_URL` = `https://aiii-five.vercel.app`
6. Deploy.

## Struktur

```
frontend/
├── app/                  # App Router: layout, page, global CSS
├── components/           # Semua UI (Header, chart, panel indikator, dst)
├── lib/                  # API client, types, analysis engine (pure functions)
├── hooks/                # useMarketData (fetch + polling + error handling)
└── .env.example
```

## Catatan

- Analisis Trend/Momentum/Volatility di `lib/analysis.ts` murni diturunkan
  dari signal indikator yang dikembalikan backend -- tidak ada angka yang
  dikarang, dan sengaja tidak menghasilkan skor confidence atau sinyal
  BUY/SELL (lihat disclaimer di panel Market Analysis).
- Polling data setiap 20 detik (`hooks/useMarketData.ts`). Ubah
  `POLL_INTERVAL_MS` jika perlu.
  
