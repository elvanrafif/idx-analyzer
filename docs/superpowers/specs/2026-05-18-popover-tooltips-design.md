# Spec: Hover Popover Tooltips untuk Card Titles

**Date:** 2026-05-18
**Status:** Approved

---

## Overview

Tambahkan rich hover popover pada semua card title di aplikasi idx-analyzer. Saat user hover di atas judul card, muncul popover berisi: judul berwarna, deskripsi lengkap (apa indikator ini, cara interpretasi, konteks trading), dan badge zona referensi (overbought/oversold/threshold) bila relevan.

---

## Scope

### Cards yang mendapat popover

1. **12 Technical Indicator cards** (`tech-card-title`):
   - EMA — Moving Averages
   - MACD (12,26,9)
   - RSI (14)
   - Stochastic (14,3,3)
   - Bollinger Bands (20,2)
   - ADX (14) — Trend Strength
   - AVWAP (Anchored VWAP)
   - Relative Volume
   - OBV (On-Balance Volume)
   - ATR (14) Volatility
   - MFI (14) Money Flow Index
   - Williams %R (14)

2. **Section titles** (dalam `sec()` function):
   - TECHNICAL INDICATORS
   - PIOTROSKI F-SCORE
   - ALTMAN Z-SCORE
   - COMPOSITE SCORE
   - TECHNICAL CONSENSUS
   - KEY LEVELS
   - TRADING OUTLOOK

3. **Key Metrics cards** (`metric-card-title`):
   - STATS
   - SCORING

---

## Data Layer

Satu object `TOOLTIPS` di `static/app.js`, dideklarasikan sebelum `renderTechnical()`. Setiap entry:

```js
var TOOLTIPS = {
  ema: {
    title: 'EMA — Moving Averages',
    desc: 'Exponential Moving Average memberi bobot lebih pada harga terbaru. Digunakan untuk menentukan tren dan level support/resistance dinamis. Golden Cross (EMA50 menembus EMA200 ke atas) sinyal bullish kuat; Death Cross sebaliknya.',
    refs: [
      { label: 'Harga > EMA200 = Uptrend', color: 'pos' },
      { label: 'Harga < EMA200 = Downtrend', color: 'neg' }
    ]
  },
  // ... dst
};
```

Field `refs` opsional — dikosongkan untuk section titles dan metric cards yang tidak punya zona numerik.

Bahasa: seluruh konten tooltip dalam **Bahasa Indonesia**.

---

## Component Structure

Helper function `tipTitle(key, displayHtml)` menghasilkan HTML berikut:

```html
<div class="tip-wrap">
  <div class="tech-card-title">{displayHtml} <span class="tip-icon">ⓘ</span></div>
  <div class="tip-box">
    <div class="tip-title">{TOOLTIPS[key].title}</div>
    <div class="tip-desc">{TOOLTIPS[key].desc}</div>
    <!-- hanya bila refs ada -->
    <div class="tip-refs">
      <span class="tip-ref {color}">{label}</span>
      ...
    </div>
  </div>
</div>
```

Untuk `section-title`: fungsi `sec(icon, title, body, open, tooltipKey)` ditambah parameter opsional `tooltipKey`. Bila ada, title dibungkus `tip-wrap` sebelum dirender.

Untuk `metric-card-title`: fungsi `metricCard(title, rows, tooltipKey)` ditambah parameter opsional `tooltipKey` yang sama.

---

## CSS

Ditambahkan ke `static/style.css`:

```css
.tip-wrap { position: relative; display: inline-block; }

.tip-icon {
  font-size: 9px; color: var(--text-secondary);
  opacity: 0.5; margin-left: 4px;
  transition: opacity .2s;
}
.tip-wrap:hover .tip-icon { opacity: 1; }

.tip-box {
  position: absolute; top: calc(100% + 6px); left: 0; z-index: 100;
  width: 260px;
  background: var(--surface); border: 1px solid var(--border-mid);
  border-radius: 8px; padding: 12px 14px;
  box-shadow: 0 8px 24px rgba(0,0,0,.6);
  opacity: 0; pointer-events: none;
  transition: opacity .15s, transform .15s;
  transform: translateY(-4px);
}
.tip-wrap:hover .tip-box {
  opacity: 1; pointer-events: auto;
  transform: translateY(0);
}

.tip-title {
  font-size: 10px; font-weight: 700; color: var(--pos);
  letter-spacing: .6px; margin-bottom: 6px;
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

### Overflow handling

Untuk card di kolom kanan (tepi viewport), tambahkan class `.tip-right` pada `.tip-wrap` yang menggeser popover ke kiri:

```css
.tip-wrap.tip-right .tip-box { left: auto; right: 0; }
```

Kolom kanan di 3-column grid (index 2, 5, 8, 11) mendapat class ini secara statis saat HTML di-generate.

---

## Perubahan File

| File | Perubahan |
|------|-----------|
| `static/app.js` | Tambah object `TOOLTIPS` (semua konten), fungsi `tipTitle()`, update 12 tech card titles, update `sec()` untuk section titles yang relevan, update `metricCard()` |
| `static/style.css` | Tambah CSS block untuk `.tip-wrap`, `.tip-box`, `.tip-title`, `.tip-desc`, `.tip-refs`, `.tip-ref` |

---

## Konten Tooltip (ringkasan)

| Key | Refs |
|-----|------|
| ema | Uptrend/Downtrend vs EMA200 |
| macd | Histogram positif/negatif |
| rsi | >70 Overbought, <30 Oversold |
| stoch | >80 Overbought, <20 Oversold |
| bb | %B >1 di atas upper, <0 di bawah lower |
| adx | >25 Tren kuat, <20 Tren lemah |
| avwap | Harga > AVWAP bullish, < bearish |
| rvol | >2x Volume tinggi, <0.7x Volume rendah |
| obv | OBV naik = akumulasi, turun = distribusi |
| atr | ATR % tinggi = volatilitas tinggi |
| mfi | >80 Overbought, <20 Oversold |
| willr | >-20 Overbought, <-80 Oversold |
| piotroski | (section — no refs) |
| altman | Z >2.99 Safe, <1.81 Distress |
| composite | (section — no refs) |
| stats | (metric card — no refs) |
| scoring | (metric card — no refs) |
