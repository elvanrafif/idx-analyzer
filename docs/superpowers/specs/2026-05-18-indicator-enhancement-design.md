# IDX Analyzer — Indicator Enhancement Design

**Date:** 2026-05-18
**Scope:** Add ATR, MFI, Williams %R; fix composite technical scoring; update stop loss; add Dividend Yield & EV/EBITDA to fundamental.

---

## Background

The analyzer already has 9 technical indicators (RSI, MACD, BB, Stochastic, ADX, OBV, AVWAP, SMA, RVOL) but only MACD + BB feed into the composite score. RSI, ADX, Stochastic, and OBV are calculated but ignored. This enhancement fixes that gap and adds three new indicators.

---

## Layer 1 — New Indicators

Three new files, each self-contained and consistent with existing indicator style.

### `indicators/atr.py`
- **Formula:** Wilder's ATR(14) — `max(High-Low, |High-PrevClose|, |Low-PrevClose|)` smoothed with Wilder's method (SMA seed + rolling average)
- **Output:**
  ```python
  {
    'value': float,       # ATR in price units
    'pct': float,         # ATR as % of current price (ATR/Close * 100)
    'signal': str,        # 'HIGH' (>3%), 'NORMAL' (1-3%), 'LOW' (<1%)
  }
  ```
- **Data required:** `hist_6m` (sufficient warmup for ATR 14)

### `indicators/mfi.py`
- **Formula:** Money Flow Index(14) — volume-weighted RSI using typical price `(H+L+C)/3`
- **Output:**
  ```python
  {
    'value': float,       # 0-100
    'signal': str,        # 'OVERBOUGHT' (>80), 'OVERSOLD' (<20), 'NEUTRAL'
  }
  ```
- **Data required:** `hist_3m` (needs High, Low, Close, Volume)

### `indicators/williams_r.py`
- **Formula:** Williams %R(14) — `(Highest High - Close) / (Highest High - Lowest Low) * -100`
- **Output:**
  ```python
  {
    'value': float,       # -100 to 0
    'signal': str,        # 'OVERBOUGHT' (>-20), 'OVERSOLD' (<-80), 'NEUTRAL'
  }
  ```
- **Data required:** `hist_3m`

---

## Layer 2 — Fix Composite Score

### Technical Score (was: BB 50% + MACD 50%)

Each indicator returns a normalized 0-100 bullish score:

| Indicator | Weight | Scoring logic |
|---|---|---|
| MACD | 20% | BULLISH=70, BEARISH=30; adjust ±10 for histogram direction |
| RSI | 15% | Linear: RSI=30→score=80, RSI=70→score=20, RSI=50→score=50 |
| BB | 15% | `(1 - pct_b) * 100` — lower in band = more bullish |
| Stochastic | 15% | Linear: K=20→80, K=80→20; crossover bonus ±10 |
| ADX | 15% | If ADX≥25 (strong): BULLISH=70/BEARISH=30; if ADX<25 (weak): neutral=50 |
| OBV | 10% | ACCUMULATION/BULLISH_DIVERGENCE=75, DISTRIBUTION/BEARISH_DIVERGENCE=25, NEUTRAL=50 |
| MFI | 5% | Linear: MFI=20→80, MFI=80→20 |
| Williams %R | 5% | Linear: W%R=-80→80, W%R=-20→20 |

`tech_score = weighted_average(all_above)`

### Composite Weights (updated)

| Component | Old | New |
|---|---|---|
| Fundamental | 30% | 28% |
| Technical | 25% | 32% |
| Risk | 20% | 20% |
| Momentum | 15% | 13% |
| Sentiment | 10% | 7% |

---

## Layer 3 — UI Update

### Technical Grid
Three new cards appended to the existing 9-card grid (slots 10, 11, 12):

**Card 10 — ATR**
- Shows: ATR value (in Rp), ATR%, volatility signal badge
- Color: HIGH=red, NORMAL=yellow, LOW=green

**Card 11 — MFI**
- Shows: value (0-100), signal badge, progress bar (same style as RSI)

**Card 12 — Williams %R**
- Shows: value (-100 to 0), signal badge, gauge bar

### Stop Loss in Outlook (`indicators/key_levels.py`)
Replace pivot-based stop loss with ATR-based:
```
stop_loss = entry_mid - (2 × ATR value)
sl_pct    = (2 × ATR value) / entry_mid × 100
```
ATR must be passed into `calculate_outlook()` as a new parameter. If ATR is unavailable, fall back to current pivot-based method.

---

## Layer 4 — Fundamental Enhancement

### `indicators/fundamental.py` (new file)

Two functions extracted here so `composite.py` doesn't grow further:

**`calculate_dividend_yield(info)`**
```python
{
  'yield': float,         # e.g. 0.045 = 4.5%
  'yield_pct': float,     # e.g. 4.5
  'signal': str,          # 'MENARIK' (>4%), 'MODERAT' (2-4%), 'RENDAH' (<2%), 'TIDAK ADA'
}
```

**`calculate_ev_ebitda(info)`**
```python
{
  'value': float,         # EV/EBITDA ratio
  'signal': str,          # 'MURAH' (<8), 'WAJAR' (8-15), 'MAHAL' (>15)
}
```

Both use `info` from yfinance (`dividendYield`, `enterpriseToEbitda`) — no extra API calls needed.

### Fundamental Score Update (in `composite.py`)
Add EV/EBITDA and Dividend Yield to `f_base` calculation:
- EV/EBITDA < 8: +5 pts bonus; > 15: -5 pts penalty
- Dividend Yield > 4%: +5 pts bonus; no dividend: 0 (not penalized)

### UI
Both metrics displayed in the **Key Metrics section** (already exists), alongside FCF Yield.

---

## Implementation Order

1. `indicators/atr.py`
2. `indicators/mfi.py`
3. `indicators/williams_r.py`
4. `indicators/fundamental.py`
5. `indicators/composite.py` — fix technical scoring + new weights + fundamental bonus
6. `indicators/key_levels.py` — ATR-based stop loss
7. `app.py` — wire up all new indicators
8. `templates/index.html` + `static/app.js` — UI for 3 new grid cards + 2 new fundamental metrics

Each layer committed separately.

---

## What Is Not Changing

- Existing indicator implementations (RSI, MACD, BB, Stochastic, ADX, OBV, AVWAP, SMA, RVOL) — already verified accurate
- Data fetching in `services/yahoo_fetcher.py` — all required data already fetched
- Piotroski, Altman Z, Sharpe, Sortino — unchanged
- Signal thresholds and labels for existing indicators — unchanged
