# AI Market Intelligence Terminal — Backend (Phase 0–2, sebagian)

Status implementasi nyata (bukan mockup) per spek `ROLE/OBJECTIVE` yang diberikan.

## Cara menjalankan test

```bash
cd backend
python3 -m unittest discover -s tests -v
```

26 test, semuanya lulus (dijalankan di sandbox: Python 3.12, `numpy`/`pandas`/`requests`,
tanpa network — semua test di-mock di layer HTTP, tidak memanggil Binance sungguhan).

## Implemented (nyata, dites)

- `app/domain/models.py` — `MarketSnapshot`, `Candle`, validasi OHLC konsisten,
  status LIVE/STALE/UNAVAILABLE berbasis umur data.
- `app/core/exceptions.py` — hierarchy error (timeout, rate limit, invalid symbol,
  unsupported timeframe, outage, malformed response, insufficient data).
- `app/providers/base.py` — interface `MarketDataProvider` (abstraction layer, spek §4).
- `app/providers/binance.py` — implementasi nyata: `GET /api/v3/klines`,
  `GET /api/v3/ticker/24hr`, mapping timeframe yang BENAR-benar didukung Binance
  spot (tidak mengklaim 2H/6H/12H karena Binance spot klines tidak native
  menyediakannya), mapping error HTTP → exception yang tepat.
- `app/cache/base.py` — `InMemoryCache` (jalan, dites via provider tests tidak
  langsung tapi struktur siap dipakai) + kerangka `RedisCache` untuk production.
- `app/indicators/trend.py` — SMA, EMA, VWAP (matematika nyata via pandas/numpy).
- `app/indicators/momentum.py` — RSI (Wilder smoothing), MACD, Stochastic, CCI.
- `app/indicators/volatility.py` — ATR (Wilder smoothing), Bollinger Bands.
- `app/indicators/volume.py` — OBV, Volume MA + deteksi anomaly volume.

Setiap indikator mengembalikan `{value, signal, interpretation, timeframe}`
sesuai spek §6 — tidak ada indikator yang hanya mengembalikan angka mentah.

## Modified

Tidak ada (project baru, tidak ada file existing untuk dimodifikasi — sudah
dikonfirmasi via audit environment sebelumnya).

## Added (dependency baru)

`numpy`, `pandas`, `requests` — sudah tersedia di sandbox ini.
`fastapi`, `pydantic`, `redis`, `sqlalchemy`, `alembic`, `celery`, `httpx` — **belum
terpasang**, lihat `requirements.txt`. Diperlukan untuk melanjutkan ke Phase 1
lanjutan (API layer) dan Phase 3+ (order book, derivatives, news scheduler).

## Tests

```
python3 -m unittest discover -s tests -v
Ran 26 tests in 0.018s
OK
```

Cakupan: parsing/normalisasi Binance provider (klines + ticker, termasuk 7
skenario error), dan matematika semua indikator (SMA/EMA/VWAP/RSI/MACD/
Stochastic/CCI/ATR/Bollinger/OBV/VolumeMA) terhadap kasus yang bisa
diverifikasi manual (all-gain RSI harus 100, flat series Bollinger width
harus 0, dst).

## Known Limitations

- **Belum ada API layer (FastAPI).** `fastapi` tidak terpasang di sandbox ini
  (tidak ada akses network untuk `pip install`). Kode indicator/provider di
  atas sudah siap dipanggil dari endpoint FastAPI — tinggal dibuatkan
  route-nya begitu dependency tersedia.
- **Binance provider belum pernah dites terhadap API sungguhan** (sandbox ini
  tanpa network egress). Parsing sudah divalidasi ketat terhadap format
  response resmi Binance via fixture, tapi verifikasi end-to-end perlu
  dilakukan di environment dengan akses internet.
- **TwelveData/OANDA (forex) belum diimplementasikan** — baru Binance
  (crypto) yang selesai di Phase 1 ini.
- **Market Structure Engine, Liquidity Engine, Order Book, Derivatives, News,
  Economic Calendar, AI Reasoning Engine, Frontend** belum dikerjakan —
  ini di luar cakupan Phase 1–2 yang selesai sesi ini.
- **Redis belum terpasang** — `RedisCache` ditulis lengkap tapi hanya
  kerangka, `InMemoryCache` yang dipakai untuk saat ini.
- **Auth, database persistence, rate limiting** belum diimplementasikan
  (bagian dari Phase 1 lanjutan setelah FastAPI tersedia).

## Next Priority

1. Setup FastAPI + expose `GET /api/v1/market-data/{symbol}` dan
   `GET /api/v1/indicators/{symbol}` yang memanggil `BinanceProvider` +
   modul indicator di atas (butuh `pip install fastapi uvicorn` di
   environment dengan network).
2. Implementasikan provider forex (TwelveData) supaya XAUUSD/EURUSD dkk
   tidak hanya crypto yang berfungsi.
3. Mulai Market Structure Engine (swing high/low, BOS/CHoCH) — ini fondasi
   untuk Confluence Engine & AI Reasoning Engine di fase berikutnya.
