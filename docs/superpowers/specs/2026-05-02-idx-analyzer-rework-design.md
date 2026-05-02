# IDX Analyzer — UI/UX Total Rework Design

**Date:** 2026-05-02
**Status:** Approved
**Approach:** Modular Refactor + UI Redesign + AI Integration

---

## 1. Overview

Perombakan total IDX Analyzer dengan fokus:
- UI/UX redesign ke **Balanced Glassmorphism** (dark mode default, glass cards, blur effects)
- Pecah `app.py` monster (~1116 baris) jadi struktur modular
- Integrasi AI analysis per section menggunakan **GLM4.1 Air**
- Perbaikan akurasi perhitungan indikator
- Trim metrics yang kurang relevan

Tech stack tetap sama: Flask + inline rendering (tanpa framework frontend baru).

---

## 2. File Architecture

```
idx-analyzer/
├── app.py                  # Flask routes, orchestrator
├── services/
│   ├── __init__.py
│   ├── yahoo_fetcher.py    # Centralized yfinance data fetching
│   └── ai_analyzer.py      # GLM4.1 Air API integration
├── indicators/
│   ├── __init__.py
│   ├── piotroski.py        # Piotroski F-Score
│   ├── altman_z.py         # Altman Z-Score
│   ├── macd_bb.py          # MACD + Bollinger Bands
│   ├── rsi.py              # RSI (14-day)
│   ├── sma.py              # EMA20, SMA50, SMA200
│   ├── rvol.py             # Relative Volume
│   ├── risk_metrics.py     # Sharpe, Sortino, FCF Yield
│   └── composite.py        # Composite Investment Score
├── templates/
│   └── index.html          # Main HTML (glassmorphism UI)
├── static/
│   ├── style.css           # CSS
│   └── app.js              # Frontend JS
├── requirements.txt
├── Dockerfile
├── .env                    # GLM_API_KEY, RISK_FREE_RATE
└── .gitignore
```

---

## 3. UI Design — Balanced Glassmorphism

### 3.1 Visual Style

- **Dark mode default** with light mode toggle
- Glass card effect: `background: rgba(255,255,255,0.05); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08)`
- Rounded corners: 12-16px
- Font: Plus Jakarta Sans (UI) + JetBrains Mono (numbers/data)
- Color palette: slate/zinc base, blue accent (#60a5fa), green positive (#34d399), red negative (#f87171), yellow warning (#fbbf24)

### 3.2 Page Layout (Top to Bottom)

1. **Hero Card** — glass card: nama saham, harga, perubahan %, sektor/industry tags
2. **Key Metrics** — grid 2 kolom: fundamental metrics + scoring summary
3. **Composite Score** — large score number + progress bars per komponen
4. **Technical Consensus** — verdict badge + indicator list + vote arrows
5. **Technical Detail** — MACD, BB, RSI, MA dalam card grid (termasuk RVOL & Risk-Adjusted)
6. **Fundamental Tabs** — 1 section dengan 4 tab: Valuasi | Profitabilitas | Kesehatan | Dividen
7. **Financial Statements Tabs** — 1 section dengan 4 tab: Income | Balance Sheet | Cash Flow | Quarterly
8. **AI Insight Box** — collapsible box di bawah setiap section

### 3.3 Section Consolidation

| Before (12+ sections) | After (7 sections) |
|---|---|
| Key Statistics | Hero Card + Key Metrics |
| Valuasi | Fundamental Tab 1 |
| Profitabilitas | Fundamental Tab 2 |
| Kesehatan Keuangan | Fundamental Tab 3 |
| Dividen | Fundamental Tab 4 |
| Technical Consensus | Technical Consensus |
| MACD/BB, RSI, MA | Technical Detail |
| RVOL | Technical Detail (sub) |
| Risk-Adjusted Return | Technical Detail (sub) |
| Piotroski F-Score | Scoring (dalam Key Metrics) |
| Altman Z-Score | Scoring (dalam Key Metrics) |
| Composite Score | Composite Score |
| Income Statement | Financial Tab 1 |
| Balance Sheet | Financial Tab 2 |
| Cash Flow | Financial Tab 3 |
| Quarterly | Financial Tab 4 |

---

## 4. AI Integration (GLM4.1 Air)

### 4.1 Backend

- **Endpoint:** `POST /api/ai-insight`
- **Request body:** `{ "ticker": "BBCA", "section": "valuasi", "data": { ... } }`
- **Service:** `services/ai_analyzer.py`
- **API:** GLM4.1 Air via REST API
- **Auth:** Bearer token dari `.env` (`GLM_API_KEY`)
- **Timeout:** 15 detik per request

### 4.2 Prompt Design

Setiap section punya prompt template yang disesuaikan:

- **Valuasi:** "Analisa valuasi saham {ticker} berdasarkan data: P/E {pe}, P/BV {pb}, PEG {peg}... Berikan insight singkat 2-3 kalimat to the point dalam Bahasa Indonesia."
- **Profitabilitas:** "Analisa profitabilitas saham {ticker}: ROE {roe}, ROA {roa}, Net Margin {npm}..."
- **Kesehatan Keuangan:** "Analisa kesehatan keuangan saham {ticker}: Current Ratio {cr}, D/E {de}..."
- **Dividen:** "Analisa dividen saham {ticker}: Yield {dy}, Payout Ratio {pr}..."
- **Technical:** "Analisa sinyal teknikal saham {ticker}: MACD {signal}, RSI {rsi}, BB {bb_signal}..."
- **Scoring:** "Interpretasi scoring saham {ticker}: Piotroski {score}/9, Altman Z {z}..."
- **Composite:** "Beri kesimpulan akhir berdasarkan composite score {score}/100..."
- **Consensus:** "Rangkum consensus teknikal: {buy} beli, {hold} netral, {sell} jual..."
- **Financial Statements:** "Tren keuangan {ticker}: revenue {trend}, profit {trend}..."

Semua prompt menghasilkan output Bahasa Indonesia, 2-3 kalimat, to the point.

### 4.3 Frontend

- Panggil `/api/ai-insight` per section secara paralel setelah data saham dimuat
- Tampilkan sebagai collapsible box (default collapsed) di bawah setiap section
- Animasi typing effect saat insight muncul
- Cache di `sessionStorage` (key: `{ticker}_{section}`) untuk menghindari double-call

---

## 5. Calculation Accuracy Fixes

### 5.1 RSI — Wilder's Smoothing

**Before:** `gain.rolling(14).mean()` (SMA-based)
**After:** `gain.ewm(alpha=1/14, adjust=False).mean()` (Wilder's Smoothing)

### 5.2 MACD — Improved Cross Detection

**Before:** Single bar histogram zero cross
**After:** Cross confirmed when histogram crosses zero AND `abs(hist) > threshold` (0.1% of price)

### 5.3 Bollinger Bands — Bandwidth

**Added metric:** `bandwidth = (upper - lower) / middle`
- Bandwidth < 0.03 = squeeze (volatility contraction, potential breakout)
- Displayed alongside %B

### 5.4 Eliminate Duplicate API Calls

**Before:** `calculate_composite()` memanggil ulang `calculate_macd_bb()` dan `yf.Ticker().history()`
**After:** Semua indicator functions menerima pre-fetched data sebagai parameter. `yahoo_fetcher.py` mengambil data sekali, distribute ke semua indicators.

### 5.5 Piotroski — Average Assets ROA

**Before:** ROA = Net Income / Total Assets (current)
**After:** ROA = Net Income / ((TA_current + TA_previous) / 2)

### 5.6 Risk-Free Rate Configurable

**Before:** Hardcoded 6.5%
**After:** `RISK_FREE_RATE` from `.env`, default 0.065

---

## 6. Metrics Trimming

### Dihapus (kurang relevan untuk analisis saham IDX)

- Shares Outstanding
- Float Shares
- Short Ratio
- Short % of Float
- Insider Holdings %
- Institution Holdings %
- EV/Revenue
- EV/EBITDA
- EPS Forward
- Gross Profit Margin (absolute)
- EBITDA Margin (absolute)
- Gross Profit (absolute)
- EBITDA (absolute)
- Revenue (absolute — growth % tetap ditampilkan)
- Book Value per Share
- 5Y Avg Dividend Yield
- Beta

### Ditambah

- Bollinger Bandwidth (squeeze detection)
- Piotroski trend indicator (naik/turun vs tahun sebelumnya)

---

## 7. Dependencies

### requirements.txt (updated)

```
flask==3.0.3
yfinance>=0.2.52
pandas==2.2.2
numpy
gunicorn==22.0.0
curl_cffi>=0.7.0
openai>=1.0.0
python-dotenv>=1.0.0
```

GLM4.1 Air API kompatibel dengan OpenAI SDK, jadi pakai library `openai`.

---

## 8. Dockerfile

Updated untuk copy struktur baru:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]
```

Timeout ditambah ke 120s karena AI API call bisa memakan waktu.
