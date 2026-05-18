# Popover Tooltips Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tambahkan rich hover popover pada semua card title (12 technical indicators, 7 section titles, 2 metric cards) yang menjelaskan indikator dalam Bahasa Indonesia.

**Architecture:** Satu object `TOOLTIPS` menyimpan semua konten. Helper `tipTitle()` menghasilkan HTML wrapper `.tip-wrap` + `.tip-box`. Show/hide via CSS `:hover` — tidak ada JS event listener. Modifikasi `sec()` dan `metricCard()` dengan parameter opsional `tooltipKey`.

**Tech Stack:** Vanilla JS (string concatenation HTML), CSS custom properties (sudah ada di codebase)

---

## File Map

| File | Perubahan |
|------|-----------|
| `static/style.css` | Tambah CSS block tooltip di bagian bawah (sebelum responsive) |
| `static/app.js` | Tambah `TOOLTIPS` + `tipTitle()` sebelum `renderTechnical()`; update 12 tech titles; update `sec()` dan `metricCard()` |

---

### Task 1: Tambah CSS tooltip ke style.css

**Files:**
- Modify: `static/style.css` — tambah block di bawah `.tech-row:last-child` (sekitar line 453), sebelum `/* ── FINANCIAL TABLE ── */`

- [ ] **Step 1: Tambah CSS block tooltip**

Buka `static/style.css`. Cari baris:
```css
/* ── FINANCIAL TABLE ── */
```
Sisipkan block berikut TEPAT sebelum komentar tersebut:

```css
/* ── TOOLTIPS ── */
.tip-wrap { position: relative; }
div.tip-wrap { display: block; }
span.tip-wrap { display: inline-flex; align-items: center; }
.tip-icon {
  font-size: 9px; color: var(--text-secondary);
  opacity: 0.4; margin-left: 4px; cursor: default;
  transition: opacity .2s; flex-shrink: 0;
}
.tip-wrap:hover .tip-icon { opacity: 1; }
.tip-box {
  position: absolute; top: calc(100% + 6px); left: 0; z-index: 200;
  width: 260px;
  background: var(--surface); border: 1px solid var(--border-mid);
  border-radius: 8px; padding: 12px 14px;
  box-shadow: 0 8px 24px rgba(0,0,0,.6);
  opacity: 0; pointer-events: none;
  transition: opacity .15s, transform .15s;
  transform: translateY(-4px);
}
.tip-wrap:hover .tip-box { opacity: 1; pointer-events: auto; transform: translateY(0); }
.tip-wrap.tip-right .tip-box { left: auto; right: 0; }
.tip-title {
  font-size: 10px; font-weight: 700; color: var(--pos);
  letter-spacing: .6px; margin-bottom: 6px; text-transform: uppercase;
}
.tip-desc {
  font-size: 11px; color: var(--text-secondary);
  line-height: 1.6; margin-bottom: 8px;
}
.tip-refs { display: flex; flex-wrap: wrap; gap: 6px; }
.tip-ref {
  font-size: 9px; font-weight: 600;
  padding: 2px 8px; border-radius: 4px;
}
.tip-ref.pos { background: var(--badge-pos-bg); color: var(--pos); }
.tip-ref.neg { background: var(--badge-neg-bg); color: var(--neg); }
.tip-ref.warn { background: var(--badge-warn-bg); color: var(--warn); }
.tip-ref.info { background: var(--badge-info-bg); color: var(--info); }
```

- [ ] **Step 2: Commit**

```bash
git add static/style.css
git commit -m "feat: add tooltip CSS styles"
```

---

### Task 2: Tambah TOOLTIPS object dan tipTitle() helper ke app.js

**Files:**
- Modify: `static/app.js` — insert sebelum `function renderTechnical(` (sekitar line 399)

- [ ] **Step 1: Insert TOOLTIPS object dan tipTitle() helper**

Cari baris `function renderTechnical(mb, rsi, sma,` di `static/app.js`. Sisipkan block berikut TEPAT sebelum baris itu:

```js
var TOOLTIPS = {
  ema: {
    title: 'EMA — Moving Averages',
    desc: 'Exponential Moving Average memberi bobot lebih pada harga terbaru dibanding SMA biasa. Digunakan untuk menentukan arah tren, level support/resistance dinamis, dan sinyal entry/exit. EMA50 dan EMA200 paling diperhatikan oleh institusi besar.',
    refs: [
      { label: 'Harga > EMA200 = Uptrend', color: 'pos' },
      { label: 'Harga < EMA200 = Downtrend', color: 'neg' },
      { label: 'Golden Cross = Bullish kuat', color: 'pos' },
      { label: 'Death Cross = Bearish kuat', color: 'neg' }
    ]
  },
  macd: {
    title: 'MACD (12,26,9)',
    desc: 'Moving Average Convergence Divergence mengukur momentum dengan selisih EMA12 dan EMA26. Histogram positif berarti momentum bullish menguat; negatif berarti bearish. Sinyal terkuat saat histogram berbalik arah dari nilai ekstrem.',
    refs: [
      { label: 'Histogram > 0 & naik = Bullish', color: 'pos' },
      { label: 'Histogram < 0 & turun = Bearish', color: 'neg' },
      { label: 'MACD cross Signal dari bawah = Beli', color: 'info' }
    ]
  },
  rsi: {
    title: 'RSI (14) — Relative Strength Index',
    desc: 'RSI mengukur kecepatan dan besar perubahan harga pada skala 0–100. Berguna untuk mengidentifikasi kondisi jenuh beli (overbought) dan jenuh jual (oversold). Divergensi RSI dengan harga sering menjadi sinyal pembalikan awal sebelum harga bergerak.',
    refs: [
      { label: '> 70 Overbought', color: 'warn' },
      { label: '< 30 Oversold', color: 'info' },
      { label: '40–60 Zona netral', color: 'pos' }
    ]
  },
  stoch: {
    title: 'Stochastic (14,3,3)',
    desc: 'Stochastic Oscillator membandingkan harga penutupan dengan rentang harga dalam periode tertentu. %K adalah nilai utama, %D adalah sinyal (moving average dari %K). Sinyal terbaik: %K memotong %D dari bawah di zona oversold (sinyal beli), atau dari atas di zona overbought (sinyal jual).',
    refs: [
      { label: '> 80 Overbought', color: 'warn' },
      { label: '< 20 Oversold', color: 'info' }
    ]
  },
  bb: {
    title: 'Bollinger Bands (20,2)',
    desc: 'Bollinger Bands terdiri dari SMA20 sebagai garis tengah dan dua band berjarak 2 standar deviasi. Harga menyentuh upper band mengindikasikan potensi jenuh beli; lower band = jenuh jual. Bandwidth yang menyempit (squeeze) sering mendahului pergerakan harga yang besar.',
    refs: [
      { label: '%B > 1 = Di atas upper band', color: 'warn' },
      { label: '%B < 0 = Di bawah lower band', color: 'info' },
      { label: 'Squeeze aktif = Waspadai breakout', color: 'warn' }
    ]
  },
  adx: {
    title: 'ADX (14) — Average Directional Index',
    desc: 'ADX mengukur kekuatan tren, bukan arahnya. ADX > 25 berarti tren cukup kuat untuk diikuti; < 20 berarti pasar sideways dan sinyal indikator tren lain kurang reliable. +DI vs -DI menunjukkan arah tren yang sedang dominan.',
    refs: [
      { label: '> 25 Tren kuat', color: 'pos' },
      { label: '< 20 Sideways / lemah', color: 'neg' },
      { label: '+DI > -DI = Bullish', color: 'pos' },
      { label: '-DI > +DI = Bearish', color: 'neg' }
    ]
  },
  avwap: {
    title: 'AVWAP — Anchored VWAP',
    desc: 'Anchored VWAP menghitung rata-rata harga tertimbang volume sejak titik acuan tertentu (biasanya awal tahun atau titik swing signifikan). Lebih akurat dari moving average karena mempertimbangkan volume. Digunakan institusi besar sebagai acuan harga wajar.',
    refs: [
      { label: 'Harga > AVWAP = Bullish bias', color: 'pos' },
      { label: 'Harga < AVWAP = Bearish bias', color: 'neg' }
    ]
  },
  rvol: {
    title: 'Relative Volume',
    desc: 'Relative Volume (RVOL) membandingkan volume hari ini dengan rata-rata 20 hari. RVOL > 2x menunjukkan aktivitas tidak biasa yang bisa menjadi sinyal breakout atau distribusi besar. RVOL rendah di tengah kenaikan harga mengindikasikan kenaikan kurang meyakinkan.',
    refs: [
      { label: '> 2x Volume sangat tinggi', color: 'warn' },
      { label: '0.8–1.2x Normal', color: 'pos' },
      { label: '< 0.7x Volume sepi', color: 'neg' }
    ]
  },
  obv: {
    title: 'OBV — On-Balance Volume',
    desc: 'OBV mengakumulasi volume: ditambahkan saat harga naik, dikurangkan saat turun. Mengungkap apakah volume mengkonfirmasi pergerakan harga. OBV naik lebih dulu sebelum harga naik sering menjadi sinyal akumulasi diam-diam oleh smart money.',
    refs: [
      { label: 'OBV naik = Akumulasi', color: 'pos' },
      { label: 'OBV turun = Distribusi', color: 'neg' },
      { label: 'Divergensi OBV-harga = Sinyal pembalikan', color: 'warn' }
    ]
  },
  atr: {
    title: 'ATR (14) — Average True Range',
    desc: 'ATR mengukur volatilitas rata-rata pergerakan harga dalam N periode — bukan arah, hanya besar pergerakan. Sangat berguna untuk menentukan ukuran stop loss yang realistis. Stop loss terlalu dekat pada saham dengan ATR tinggi sering terkena noise pasar.',
    refs: [
      { label: 'ATR % tinggi = Volatilitas tinggi', color: 'warn' },
      { label: 'ATR % rendah = Pasar tenang', color: 'info' }
    ]
  },
  mfi: {
    title: 'MFI (14) — Money Flow Index',
    desc: 'Money Flow Index adalah RSI berbasis volume — mengukur tekanan beli/jual dengan mempertimbangkan volume transaksi. Lebih akurat dari RSI murni untuk saham dengan volume tidak konsisten. Divergensi MFI dengan harga adalah sinyal pembalikan yang kuat.',
    refs: [
      { label: '> 80 Overbought', color: 'warn' },
      { label: '< 20 Oversold', color: 'info' }
    ]
  },
  willr: {
    title: 'Williams %R (14)',
    desc: 'Williams %R mengukur posisi harga penutupan relatif terhadap rentang harga tertinggi dalam periode tertentu. Nilai berkisar -100 hingga 0 (kebalikan dari Stochastic). Paling efektif digunakan sebagai konfirmasi sinyal reversal dari indikator lain.',
    refs: [
      { label: '> -20 Overbought', color: 'warn' },
      { label: '< -80 Oversold', color: 'info' }
    ]
  },
  technical_indicators: {
    title: 'Technical Indicators',
    desc: 'Kumpulan indikator teknikal yang menganalisis pergerakan harga dan volume historis untuk mengidentifikasi tren, momentum, volatilitas, dan potensi pembalikan. Digunakan untuk timing entry/exit dan konfirmasi sinyal trading.',
    refs: []
  },
  piotroski: {
    title: 'Piotroski F-Score',
    desc: 'Sistem penilaian fundamental yang menggunakan 9 kriteria dari laporan keuangan: profitabilitas (ROA, OCF, akrual), leverage (debt ratio, current ratio, dilusi saham), dan efisiensi (gross margin, asset turnover). Skor 1 poin per kriteria yang terpenuhi.',
    refs: [
      { label: '7–9 Fundamental kuat', color: 'pos' },
      { label: '3–6 Sedang', color: 'warn' },
      { label: '0–2 Fundamental lemah', color: 'neg' }
    ]
  },
  altman: {
    title: 'Altman Z-Score',
    desc: 'Formula prediksi kebangkrutan yang dikembangkan Edward Altman (1968). Mengkombinasikan 5 rasio keuangan: working capital, retained earnings, EBIT, market cap, dan revenue terhadap total aset. Efektif untuk perusahaan manufaktur; gunakan dengan hati-hati untuk sektor keuangan.',
    refs: [
      { label: '> 2.99 Safe zone', color: 'pos' },
      { label: '1.81–2.99 Grey zone', color: 'warn' },
      { label: '< 1.81 Distress zone', color: 'neg' }
    ]
  },
  composite: {
    title: 'Composite Score',
    desc: 'Skor gabungan yang mengkombinasikan sinyal dari semua 12 indikator teknikal menjadi satu angka terbobot. Bobot masing-masing indikator dikalibrasi untuk konteks pasar IDX. Skor tinggi = mayoritas indikator menunjukkan sinyal bullish.',
    refs: []
  },
  consensus: {
    title: 'Technical Consensus',
    desc: 'Ringkasan arah keseluruhan dari semua indikator teknikal — berapa yang memberikan sinyal bullish, bearish, dan netral. Berguna sebagai pandangan cepat tanpa harus membaca setiap indikator satu per satu.',
    refs: []
  },
  key_levels: {
    title: 'Key Levels',
    desc: 'Level-level harga penting yang bertindak sebagai support (lantai harga) dan resistance (atap harga). Bersumber dari pivot point, high/low historis, dan level psikologis. Berguna untuk menentukan target profit dan penempatan stop loss.',
    refs: []
  },
  outlook: {
    title: 'Trading Outlook',
    desc: 'Rekomendasi trading berdasarkan analisis gabungan indikator teknikal, level kunci, dan kondisi pasar. Mencakup saran posisi (beli/jual/tunggu), level entry yang disarankan, target profit, dan stop loss berbasis ATR.',
    refs: []
  },
  stats: {
    title: 'Key Stats',
    desc: 'Data fundamental utama perusahaan: valuasi (P/E trailing & forward, P/BV, PEG), profitabilitas (ROE, ROA, net margin, operating margin), pertumbuhan revenue & earnings YoY, dan kesehatan keuangan (current ratio, debt-to-equity, free cash flow).',
    refs: []
  },
  scoring: {
    title: 'Scoring & Targets',
    desc: 'Skor-skor kuantitatif dari model analisis: Piotroski F-Score (kekuatan fundamental 0–9), Altman Z-Score (risiko kebangkrutan), dividend yield, EV/EBITDA (valuasi relatif terhadap earning), dan estimasi upside dari target harga konsensus analis.',
    refs: []
  }
};

function tipTitle(key, displayHtml, alignRight) {
  var t = TOOLTIPS[key];
  if (!t) return '<div class="tech-card-title">' + displayHtml + '</div>';
  var refsHtml = '';
  if (t.refs && t.refs.length) {
    refsHtml = '<div class="tip-refs">' +
      t.refs.map(function(r) { return '<span class="tip-ref ' + r.color + '">' + r.label + '</span>'; }).join('') +
    '</div>';
  }
  return '<div class="tip-wrap' + (alignRight ? ' tip-right' : '') + '">' +
    '<div class="tech-card-title">' + displayHtml + ' <span class="tip-icon">ⓘ</span></div>' +
    '<div class="tip-box">' +
      '<div class="tip-title">' + t.title + '</div>' +
      '<div class="tip-desc">' + t.desc + '</div>' +
      refsHtml +
    '</div>' +
  '</div>';
}

function secTipTitle(key, labelHtml) {
  var t = TOOLTIPS[key];
  if (!t) return labelHtml;
  var refsHtml = '';
  if (t.refs && t.refs.length) {
    refsHtml = '<div class="tip-refs" style="margin-top:6px;">' +
      t.refs.map(function(r) { return '<span class="tip-ref ' + r.color + '">' + r.label + '</span>'; }).join('') +
    '</div>';
  }
  return '<span class="tip-wrap">' +
    labelHtml + ' <span class="tip-icon">ⓘ</span>' +
    '<div class="tip-box">' +
      '<div class="tip-title">' + t.title + '</div>' +
      '<div class="tip-desc">' + t.desc + '</div>' +
      refsHtml +
    '</div>' +
  '</span>';
}
```

- [ ] **Step 2: Commit**

```bash
git add static/app.js
git commit -m "feat: add TOOLTIPS data object and tipTitle helpers"
```

---

### Task 3: Update 12 technical card titles

**Files:**
- Modify: `static/app.js` — update `renderTechnical()` function

Ganti setiap `'<div class="tech-card-title">...'` dengan panggilan `tipTitle()`.

Perhatian: cards di kolom kanan grid (posisi ke-3, ke-6, ke-9, ke-12 — yaitu index 2, 5, 8, 11 dalam array `cards`) perlu argumen `true` sebagai parameter `alignRight` agar popover tidak keluar viewport.

Urutan cards: EMA(0), MACD(1), RSI(2✓), Stoch(3), BB(4), ADX(5✓), AVWAP(6), RVOL(7), OBV(8✓), ATR(9), MFI(10), WillR(11✓)

- [ ] **Step 1: Ganti 12 tech-card-title**

Buka `static/app.js`. Lakukan penggantian berikut satu per satu:

**1. EMA (index 0 — kiri):**
```js
// SEBELUM:
'<div class="tech-card-title">EMA — Moving Averages</div>' +
// SESUDAH:
tipTitle('ema', 'EMA — Moving Averages') +
```

**2. MACD (index 1 — tengah):**
```js
// SEBELUM:
'<div class="tech-card-title">MACD (12,26,9)</div>' +
// SESUDAH:
tipTitle('macd', 'MACD (12,26,9)') +
```

**3. RSI (index 2 — kanan, alignRight=true):**
```js
// SEBELUM:
'<div class="tech-card-title">RSI (14)</div>' +
// SESUDAH:
tipTitle('rsi', 'RSI (14)', true) +
```

**4. Stochastic (index 3 — kiri):**
```js
// SEBELUM:
'<div class="tech-card-title">Stochastic (14,3,3)</div>' +
// SESUDAH:
tipTitle('stoch', 'Stochastic (14,3,3)') +
```

**5. Bollinger Bands (index 4 — tengah):**
```js
// SEBELUM:
'<div class="tech-card-title">Bollinger Bands (20,2)</div>' +
// SESUDAH:
tipTitle('bb', 'Bollinger Bands (20,2)') +
```

**6. ADX (index 5 — kanan, alignRight=true):**
```js
// SEBELUM:
'<div class="tech-card-title">ADX (14) — Trend Strength</div>' +
// SESUDAH:
tipTitle('adx', 'ADX (14) — Trend Strength', true) +
```

**7. AVWAP (index 6 — kiri):**
```js
// SEBELUM:
'<div class="tech-card-title">AVWAP <span style="font-size:9px;opacity:.6;">(Anchored VWAP)</span></div>' +
// SESUDAH:
tipTitle('avwap', 'AVWAP <span style="font-size:9px;opacity:.6;">(Anchored VWAP)</span>') +
```

**8. Relative Volume (index 7 — tengah):**
```js
// SEBELUM:
'<div class="tech-card-title">Relative Volume</div>' +
// SESUDAH:
tipTitle('rvol', 'Relative Volume') +
```

**9. OBV (index 8 — kanan, alignRight=true):**
```js
// SEBELUM:
'<div class="tech-card-title">OBV <span style="font-size:9px;opacity:.6;">(On-Balance Volume)</span></div>' +
// SESUDAH:
tipTitle('obv', 'OBV <span style="font-size:9px;opacity:.6;">(On-Balance Volume)</span>', true) +
```

**10. ATR (index 9 — kiri):**
```js
// SEBELUM:
'<div class="tech-card-title">ATR (14) <span style="font-size:9px;opacity:.6;">Volatility</span></div>' +
// SESUDAH:
tipTitle('atr', 'ATR (14) <span style="font-size:9px;opacity:.6;">Volatility</span>') +
```

**11. MFI (index 10 — tengah):**
```js
// SEBELUM:
'<div class="tech-card-title">MFI (14) <span style="font-size:9px;opacity:.6;">Money Flow Index</span></div>' +
// SESUDAH:
tipTitle('mfi', 'MFI (14) <span style="font-size:9px;opacity:.6;">Money Flow Index</span>') +
```

**12. Williams %R (index 11 — kanan, alignRight=true):**
```js
// SEBELUM:
'<div class="tech-card-title">Williams %R (14)</div>' +
// SESUDAH:
tipTitle('willr', 'Williams %R (14)', true) +
```

- [ ] **Step 2: Commit**

```bash
git add static/app.js
git commit -m "feat: add hover tooltips to all 12 technical indicator cards"
```

---

### Task 4: Update sec() dan metricCard() untuk section + metric tooltips

**Files:**
- Modify: `static/app.js` — fungsi `sec()` (line ~81) dan `metricCard()` (line ~285–289), plus call sites di `renderPage()`

- [ ] **Step 1: Update fungsi sec() untuk terima tooltipKey opsional**

Cari fungsi `sec()` di `static/app.js` (sekitar line 81). Ganti seluruh fungsi:

```js
// SEBELUM:
function sec(icon, title, body, open) {
  var id = 's' + Math.random().toString(36).slice(2, 8);
  var iconHtml = icon ? '<div class="section-icon">' + icon + '</div>' : '';
  return '<div class="section glass' + (open ? '' : ' collapsed') + '" id="' + id + '">' +
    '<div class="section-header" onclick="document.getElementById(\'' + id + '\').classList.toggle(\'collapsed\')">' +
      iconHtml +
      '<div class="section-title">' + title + '</div>' +
      '<div class="section-toggle">▼</div>' +
    '</div>' +
    '<div class="section-divider"></div>' +
    '<div class="section-body">' + body + '</div>' +
  '</div>';
}

// SESUDAH:
function sec(icon, title, body, open, tooltipKey) {
  var id = 's' + Math.random().toString(36).slice(2, 8);
  var iconHtml = icon ? '<div class="section-icon">' + icon + '</div>' : '';
  var titleHtml = tooltipKey ? secTipTitle(tooltipKey, title) : title;
  return '<div class="section glass' + (open ? '' : ' collapsed') + '" id="' + id + '">' +
    '<div class="section-header" onclick="document.getElementById(\'' + id + '\').classList.toggle(\'collapsed\')">' +
      iconHtml +
      '<div class="section-title">' + titleHtml + '</div>' +
      '<div class="section-toggle">▼</div>' +
    '</div>' +
    '<div class="section-divider"></div>' +
    '<div class="section-body">' + body + '</div>' +
  '</div>';
}
```

- [ ] **Step 2: Update fungsi metricCard() untuk terima tooltipKey opsional**

Cari fungsi `metricCard()` di dalam `renderKeyMetrics()` (sekitar line 285). Ganti:

```js
// SEBELUM:
function metricCard(title, rows) {
  return '<div class="metric-card"><div class="metric-card-title">' + title + '</div>' +
    rows.map(function(r) {
      return '<div class="metric-row"><span class="metric-label">' + r[0] + '</span><span class="metric-value">' + r[1] + '</span></div>';
    }).join('') + '</div>';
}

// SESUDAH:
function metricCard(title, rows, tooltipKey) {
  var titleHtml = tooltipKey ? secTipTitle(tooltipKey, title) : title;
  return '<div class="metric-card"><div class="metric-card-title">' + titleHtml + '</div>' +
    rows.map(function(r) {
      return '<div class="metric-row"><span class="metric-label">' + r[0] + '</span><span class="metric-value">' + r[1] + '</span></div>';
    }).join('') + '</div>';
}
```

- [ ] **Step 3: Update call sites di renderPage() untuk section titles**

Cari bagian di `renderPage()` (sekitar line 961–980 di `static/app.js`). Update setiap panggilan `sec()` yang relevan dengan menambah `tooltipKey` sebagai argumen ke-5:

```js
// SEBELUM:
html += sec('', 'KEY LEVELS', renderKeyLevels(d.key_levels), true);
html += sec('', 'TRADING OUTLOOK', renderOutlook(d.outlook), true);
// SESUDAH:
html += sec('', 'KEY LEVELS', renderKeyLevels(d.key_levels), true, 'key_levels');
html += sec('', 'TRADING OUTLOOK', renderOutlook(d.outlook), true, 'outlook');
```

```js
// SEBELUM:
html += sec('', 'TECHNICAL INDICATORS', renderTechnical(...), true);
// SESUDAH:
html += sec('', 'TECHNICAL INDICATORS', renderTechnical(...), true, 'technical_indicators');
```

```js
// SEBELUM:
html += sec('', 'PIOTROSKI F-SCORE', renderPiotroski(d.piotroski), true);
html += sec('', 'ALTMAN Z-SCORE', renderAltman(d.altman), true);
// SESUDAH:
html += sec('', 'PIOTROSKI F-SCORE', renderPiotroski(d.piotroski), true, 'piotroski');
html += sec('', 'ALTMAN Z-SCORE', renderAltman(d.altman), true, 'altman');
```

```js
// SEBELUM:
html += sec('', 'TECHNICAL CONSENSUS', renderConsensus(d), true);
html += sec('', 'COMPOSITE SCORE', renderComposite(d.composite), true);
// SESUDAH:
html += sec('', 'TECHNICAL CONSENSUS', renderConsensus(d), true, 'consensus');
html += sec('', 'COMPOSITE SCORE', renderComposite(d.composite), true, 'composite');
```

- [ ] **Step 4: Update call sites metricCard() di renderKeyMetrics()**

Cari baris `return '<div class="metrics-grid">' + metricCard('STATS', left) + metricCard('SCORING', right)` (sekitar line 292). Ganti:

```js
// SEBELUM:
return '<div class="metrics-grid">' + metricCard('STATS', left) + metricCard('SCORING', right) + '</div>';
// SESUDAH:
return '<div class="metrics-grid">' + metricCard('STATS', left, 'stats') + metricCard('SCORING', right, 'scoring') + '</div>';
```

- [ ] **Step 5: Commit**

```bash
git add static/app.js
git commit -m "feat: add hover tooltips to section titles and metric cards"
```

---

### Task 5: Verifikasi manual dan push

- [ ] **Step 1: Jalankan app**

```bash
cd /Users/fadhel/Documents/projects/MyTrading/idx-analyzer
python app.py
```

Buka browser ke `http://localhost:5000` (atau port yang digunakan).

- [ ] **Step 2: Test hover di technical cards**

Cari saham (misal `BBCA` atau `BULL`). Scroll ke bagian **TECHNICAL INDICATORS**. Hover di atas judul-judul berikut dan pastikan popover muncul dengan konten yang benar:

| Card | Cek |
|------|-----|
| EMA — Moving Averages | Deskripsi + 4 badge refs |
| MACD (12,26,9) | Deskripsi + 3 badge refs |
| RSI (14) | Popover muncul ke kiri (tidak keluar viewport) |
| Stochastic (14,3,3) | Deskripsi + 2 badge refs |
| Bollinger Bands | Deskripsi + 3 badge refs |
| ADX (14) | Popover muncul ke kiri |
| AVWAP | Deskripsi + 2 badge refs |
| Relative Volume | Deskripsi + 3 badge refs |
| OBV | Popover muncul ke kiri |
| ATR (14) | Deskripsi + 2 badge refs |
| MFI (14) | Deskripsi + 2 badge refs |
| Williams %R | Popover muncul ke kiri |

- [ ] **Step 3: Test hover di section titles**

Hover di atas judul section: **TECHNICAL INDICATORS**, **PIOTROSKI F-SCORE**, **ALTMAN Z-SCORE**, **COMPOSITE SCORE**, **TECHNICAL CONSENSUS**, **KEY LEVELS**, **TRADING OUTLOOK**. Pastikan ikon ⓘ muncul dan popover berisi deskripsi yang sesuai.

- [ ] **Step 4: Test hover di Key Metrics**

Scroll ke bagian **KEY METRICS**. Hover di atas **STATS** dan **SCORING** — popover harus muncul.

- [ ] **Step 5: Test Death Cross (BBCA) masih OK**

Cari `BBCA`. Pastikan badge "Death Cross (EMA50<EMA200)" masih tampil benar (tidak breaking layout), dan tooltip EMA card juga muncul.

- [ ] **Step 6: Push**

```bash
git push origin main
```
