# Indicator Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ATR, MFI, Williams %R indicators; fix composite technical scoring to use all 8 indicators; add ATR-based stop loss; add EV/EBITDA and Dividend Yield to fundamental scoring.

**Architecture:** Four layers — (1) new indicator files, (2) composite + key_levels logic update, (3) app.py wiring, (4) UI rendering. Each layer committed separately.

**Tech Stack:** Python 3, pandas, numpy, Flask, vanilla JS (no new dependencies)

---

## File Map

| Action | File | Purpose |
|---|---|---|
| Create | `indicators/atr.py` | ATR(14) — volatility + stop loss input |
| Create | `indicators/mfi.py` | Money Flow Index(14) — volume-weighted RSI |
| Create | `indicators/williams_r.py` | Williams %R(14) — momentum oscillator |
| Create | `indicators/fundamental.py` | Dividend Yield + EV/EBITDA helpers |
| Modify | `indicators/composite.py` | Fix technical score, new weights, fundamental bonus |
| Modify | `indicators/key_levels.py` | ATR-based stop loss in calculate_outlook |
| Modify | `app.py` | Wire up all new indicators |
| Modify | `static/app.js` | 3 new tech cards, updated weights display, signal strip |

---

## Task 1: Add ATR Indicator

**Files:**
- Create: `indicators/atr.py`

- [ ] **Step 1: Create `indicators/atr.py`**

```python
def calculate_atr(hist, period=14):
    if hist is None or len(hist) < period + 2:
        return None
    try:
        hist = hist.dropna(subset=['Close', 'High', 'Low'])
        if len(hist) < period + 2:
            return None
        high  = hist['High']
        low   = hist['Low']
        close = hist['Close']

        prev_close = close.shift(1)
        tr = (high - low).combine(
            (high - prev_close).abs(), max
        ).combine(
            (low - prev_close).abs(), max
        ).dropna()

        # Wilder's smoothing: SMA seed then rolling
        atr_val = float(tr.iloc[:period].mean())
        for val in tr.iloc[period:]:
            atr_val = (atr_val * (period - 1) + val) / period

        price   = float(close.iloc[-1])
        atr_pct = round(atr_val / price * 100, 2) if price else 0

        if atr_pct > 3:
            signal = 'HIGH'
        elif atr_pct > 1:
            signal = 'NORMAL'
        else:
            signal = 'LOW'

        return {
            'value': round(atr_val, 0),
            'pct':   atr_pct,
            'signal': signal,
        }
    except:
        return None
```

- [ ] **Step 2: Verify ATR output**

```bash
cd /Users/fadhel/Documents/projects/MyTrading/idx-analyzer && python3 -c "
import yfinance as yf, pandas as pd, warnings; warnings.filterwarnings('ignore')
hist = yf.download('BBCA.JK', period='6mo', interval='1d', progress=False, auto_adjust=True)
if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
from indicators.atr import calculate_atr
r = calculate_atr(hist)
print(r)
assert r is not None, 'ATR returned None'
assert 'value' in r and 'pct' in r and 'signal' in r
assert r['signal'] in ('HIGH', 'NORMAL', 'LOW')
print('ATR OK')
"
```

Expected output: dict with `value` (Rp amount), `pct` (%), `signal` one of HIGH/NORMAL/LOW.

- [ ] **Step 3: Commit**

```bash
git add indicators/atr.py
git commit -m "feat: add ATR(14) indicator with Wilder's smoothing"
```

---

## Task 2: Add MFI Indicator

**Files:**
- Create: `indicators/mfi.py`

- [ ] **Step 1: Create `indicators/mfi.py`**

```python
def calculate_mfi(hist, period=14):
    if hist is None or len(hist) < period + 2:
        return None
    try:
        hist = hist.dropna(subset=['Close', 'High', 'Low', 'Volume'])
        if len(hist) < period + 2:
            return None
        high   = hist['High']
        low    = hist['Low']
        close  = hist['Close']
        volume = hist['Volume']

        typical = (high + low + close) / 3
        money_flow = typical * volume

        pos_mf = money_flow.where(typical > typical.shift(1), 0)
        neg_mf = money_flow.where(typical < typical.shift(1), 0)

        pos_sum = pos_mf.rolling(period).sum()
        neg_sum = neg_mf.rolling(period).sum()

        mfr = pos_sum / neg_sum.replace(0, float('nan'))
        mfi_series = 100 - (100 / (1 + mfr))

        val = round(float(mfi_series.dropna().iloc[-1]), 1)

        if val > 80:
            signal = 'OVERBOUGHT'
        elif val < 20:
            signal = 'OVERSOLD'
        else:
            signal = 'NEUTRAL'

        return {'value': val, 'signal': signal}
    except:
        return None
```

- [ ] **Step 2: Verify MFI output**

```bash
cd /Users/fadhel/Documents/projects/MyTrading/idx-analyzer && python3 -c "
import yfinance as yf, pandas as pd, warnings; warnings.filterwarnings('ignore')
hist = yf.download('BBCA.JK', period='3mo', interval='1d', progress=False, auto_adjust=True)
if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
from indicators.mfi import calculate_mfi
r = calculate_mfi(hist)
print(r)
assert r is not None, 'MFI returned None'
assert 0 <= r['value'] <= 100, 'MFI value out of range'
assert r['signal'] in ('OVERBOUGHT', 'OVERSOLD', 'NEUTRAL')
print('MFI OK')
"
```

Expected: dict with `value` 0-100 and `signal`.

- [ ] **Step 3: Commit**

```bash
git add indicators/mfi.py
git commit -m "feat: add MFI(14) Money Flow Index indicator"
```

---

## Task 3: Add Williams %R Indicator

**Files:**
- Create: `indicators/williams_r.py`

- [ ] **Step 1: Create `indicators/williams_r.py`**

```python
def calculate_williams_r(hist, period=14):
    if hist is None or len(hist) < period + 1:
        return None
    try:
        hist = hist.dropna(subset=['Close', 'High', 'Low'])
        if len(hist) < period + 1:
            return None
        high  = hist['High']
        low   = hist['Low']
        close = hist['Close']

        highest_high = high.rolling(period).max()
        lowest_low   = low.rolling(period).min()

        willr_series = (highest_high - close) / (highest_high - lowest_low) * -100
        val = round(float(willr_series.dropna().iloc[-1]), 1)

        if val > -20:
            signal = 'OVERBOUGHT'
        elif val < -80:
            signal = 'OVERSOLD'
        else:
            signal = 'NEUTRAL'

        return {'value': val, 'signal': signal}
    except:
        return None
```

- [ ] **Step 2: Verify Williams %R output**

```bash
cd /Users/fadhel/Documents/projects/MyTrading/idx-analyzer && python3 -c "
import yfinance as yf, pandas as pd, warnings; warnings.filterwarnings('ignore')
hist = yf.download('BBCA.JK', period='3mo', interval='1d', progress=False, auto_adjust=True)
if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
from indicators.williams_r import calculate_williams_r
r = calculate_williams_r(hist)
print(r)
assert r is not None, 'Williams %R returned None'
assert -100 <= r['value'] <= 0, 'Williams %R value out of range'
assert r['signal'] in ('OVERBOUGHT', 'OVERSOLD', 'NEUTRAL')
print('Williams R OK')
"
```

Expected: dict with `value` between -100 and 0, `signal`.

- [ ] **Step 3: Commit**

```bash
git add indicators/williams_r.py
git commit -m "feat: add Williams %R(14) momentum indicator"
```

---

## Task 4: Add Fundamental Helpers

**Files:**
- Create: `indicators/fundamental.py`

- [ ] **Step 1: Create `indicators/fundamental.py`**

```python
def calculate_dividend_yield(info):
    if info is None:
        return None
    try:
        dy = info.get('dividendYield')
        if dy is None:
            return {'yield': 0, 'yield_pct': 0, 'signal': 'TIDAK ADA'}
        dy = float(dy)
        pct = round(dy * 100, 2)
        if pct >= 4:
            signal = 'MENARIK'
        elif pct >= 2:
            signal = 'MODERAT'
        elif pct > 0:
            signal = 'RENDAH'
        else:
            signal = 'TIDAK ADA'
        return {'yield': dy, 'yield_pct': pct, 'signal': signal}
    except:
        return None


def calculate_ev_ebitda(info):
    if info is None:
        return None
    try:
        ev_ebitda = info.get('enterpriseToEbitda')
        if ev_ebitda is None:
            return None
        val = float(ev_ebitda)
        if val <= 0:
            return None
        if val < 8:
            signal = 'MURAH'
        elif val <= 15:
            signal = 'WAJAR'
        else:
            signal = 'MAHAL'
        return {'value': round(val, 1), 'signal': signal}
    except:
        return None
```

- [ ] **Step 2: Verify fundamental helpers**

```bash
cd /Users/fadhel/Documents/projects/MyTrading/idx-analyzer && python3 -c "
import yfinance as yf, warnings; warnings.filterwarnings('ignore')
info = yf.Ticker('BBCA.JK').info
from indicators.fundamental import calculate_dividend_yield, calculate_ev_ebitda
dy = calculate_dividend_yield(info)
ev = calculate_ev_ebitda(info)
print('DY:', dy)
print('EV/EBITDA:', ev)
assert dy is not None
assert dy['signal'] in ('MENARIK', 'MODERAT', 'RENDAH', 'TIDAK ADA')
if ev: assert ev['signal'] in ('MURAH', 'WAJAR', 'MAHAL')
print('Fundamental helpers OK')
"
```

- [ ] **Step 3: Commit**

```bash
git add indicators/fundamental.py
git commit -m "feat: add Dividend Yield and EV/EBITDA fundamental helpers"
```

---

## Task 5: Fix Composite Score

**Files:**
- Modify: `indicators/composite.py`

The function signature changes from:
`calculate_composite(info, piotroski, altman, macd_bb_data, rsi_data, sharpe, sortino, rvol_data, hist_1y)`

To:
`calculate_composite(info, piotroski, altman, macd_bb_data, rsi_data, sharpe, sortino, rvol_data, hist_1y, adx_data=None, stoch_data=None, obv_data=None, mfi_data=None, willr_data=None)`

- [ ] **Step 1: Replace `indicators/composite.py` entirely**

```python
def calculate_composite(info, piotroski, altman, macd_bb_data, rsi_data,
                         sharpe, sortino, rvol_data, hist_1y,
                         adx_data=None, stoch_data=None, obv_data=None,
                         mfi_data=None, willr_data=None):
    try:
        # --- Fundamental (28%) ---
        pe  = min(float(info.get('trailingPE') or 50), 100)
        pb  = min(float(info.get('priceToBook') or 5), 20)
        roe = float(info.get('returnOnEquity') or 0) * 100
        cr  = float(info.get('currentRatio') or 1)
        de  = float(info.get('debtToEquity') or 100)

        val_sc  = max(0, min(30, (50 - pe) / 50 * 30)) if pe > 0 else 0
        prof_sc = min(25, roe * 0.8) if roe > 0 else 0
        hlth_sc = max(0, min(20, cr / 3 * 20) - (de / 100 - 1) * 5 if cr > 0 else 0)
        f_base  = (val_sc + prof_sc + hlth_sc) / 75 * 100
        p_bonus = (piotroski['score'] / 9 * 100) if piotroski else 50
        fund    = f_base * 0.5 + p_bonus * 0.5

        # EV/EBITDA bonus/penalty
        ev_ebitda = info.get('enterpriseToEbitda')
        if ev_ebitda:
            ev = float(ev_ebitda)
            if 0 < ev < 8:
                fund = min(100, fund + 5)
            elif ev > 15:
                fund = max(0, fund - 5)

        # Dividend yield bonus
        dy = info.get('dividendYield')
        if dy and float(dy) * 100 >= 4:
            fund = min(100, fund + 5)

        # --- Technical (32%) — 8 indicators ---
        scores = []

        if macd_bb_data:
            # MACD: 20% weight
            macd_score = 70 if macd_bb_data['macd']['signal_label'] == 'BULLISH' else 30
            if macd_bb_data['macd']['hist'] > 0:
                macd_score = min(100, macd_score + 10)
            else:
                macd_score = max(0, macd_score - 10)
            scores.append((macd_score, 0.20))

            # BB: 15% weight — lower pct_b = more bullish
            bb_score = (1 - macd_bb_data['bb']['pct_b']) * 100
            scores.append((bb_score, 0.15))

        if rsi_data:
            # RSI: 15% — inverse linear (RSI 30 → 70, RSI 70 → 30)
            rsi_score = 100 - rsi_data['value']
            scores.append((rsi_score, 0.15))

        if stoch_data:
            # Stochastic: 15% — inverse of K
            stoch_score = 100 - stoch_data['k']
            if stoch_data.get('cross') == 'GOLDEN CROSS':
                stoch_score = min(100, stoch_score + 10)
            elif stoch_data.get('cross') == 'DEATH CROSS':
                stoch_score = max(0, stoch_score - 10)
            scores.append((stoch_score, 0.15))

        if adx_data:
            # ADX: 15% — strong trend direction, weak = neutral
            if adx_data['strength'] == 'WEAK':
                adx_score = 50
            elif adx_data['direction'] == 'BULLISH':
                adx_score = 70 if adx_data['strength'] == 'STRONG' else 60
            else:
                adx_score = 30 if adx_data['strength'] == 'STRONG' else 40
            scores.append((adx_score, 0.15))

        if obv_data:
            # OBV: 10%
            obv_map = {
                'ACCUMULATION': 75, 'BULLISH DIVERGENCE': 80,
                'DISTRIBUTION': 25, 'BEARISH DIVERGENCE': 20,
                'NEUTRAL': 50,
            }
            obv_score = obv_map.get(obv_data['signal'], 50)
            scores.append((obv_score, 0.10))

        if mfi_data:
            # MFI: 5% — inverse linear like RSI
            mfi_score = 100 - mfi_data['value']
            scores.append((mfi_score, 0.05))

        if willr_data:
            # Williams %R: 5% — value is -100 to 0, negate for bullish score
            willr_score = -willr_data['value']  # -(-80) = 80 (oversold=bullish)
            scores.append((willr_score, 0.05))

        if scores:
            total_weight = sum(w for _, w in scores)
            tech = sum(s * w for s, w in scores) / total_weight
        else:
            tech = 50

        # --- Risk (20%) ---
        risk = 50
        if sharpe is not None:
            risk = max(0, min(80, 40 + sharpe * 15))
        if sortino is not None:
            sor  = max(0, min(80, 40 + sortino * 15))
            risk = (risk + sor) / 2
        if altman:
            if altman['zone'] == 'AMAN':
                risk = min(100, risk + 15)
            elif altman['zone'] == 'BAHAYA':
                risk = max(0, risk - 30)

        # --- Momentum (13%) ---
        mom = 50
        if hist_1y is not None and len(hist_1y) > 126:
            try:
                h  = hist_1y['Close']
                m1 = (h.iloc[-1] / h.iloc[-22]  - 1) * 100 if len(h) > 22  else 0
                m3 = (h.iloc[-1] / h.iloc[-66]  - 1) * 100 if len(h) > 66  else 0
                m6 = (h.iloc[-1] / h.iloc[-126] - 1) * 100 if len(h) > 126 else 0
                mom = max(0, min(100, 50 + m1 * 0.3 + m3 * 0.4 + m6 * 0.3))
            except:
                pass

        # --- Sentiment (7%) ---
        sent = 50
        if rvol_data:
            sent = max(0, min(90, 50 + (rvol_data['rvol'] - 1) * 20))
        rec    = (info.get('recommendationKey') or '').lower().replace('_', '')
        boosts = {'strongbuy': 20, 'buy': 10, 'hold': 0, 'neutral': 0, 'sell': -15, 'strongsell': -25}
        sent   = max(0, min(100, sent + boosts.get(rec, 0)))

        final = round(min(100, max(0,
            fund * 0.28 + tech * 0.32 + risk * 0.20 + mom * 0.13 + sent * 0.07
        )), 1)

        if final >= 70:   sig, cls = 'STRONG BUY',  'c-sb'
        elif final >= 60: sig, cls = 'BUY',          'c-b'
        elif final >= 45: sig, cls = 'HOLD',         'c-h'
        elif final >= 35: sig, cls = 'SELL',         'c-s'
        else:             sig, cls = 'STRONG SELL',  'c-ss'

        return {
            'final': final,
            'signal': sig,
            'cls': cls,
            'components': {
                'Fundamental': round(fund, 1),
                'Technical':   round(tech, 1),
                'Risk':        round(risk, 1),
                'Momentum':    round(mom, 1),
                'Sentiment':   round(sent, 1),
            },
        }
    except:
        return None
```

- [ ] **Step 2: Verify composite still returns valid output**

```bash
cd /Users/fadhel/Documents/projects/MyTrading/idx-analyzer && python3 -c "
import yfinance as yf, pandas as pd, warnings; warnings.filterwarnings('ignore')
hist_raw = yf.download('BBCA.JK', period='1y', interval='1d', progress=False, auto_adjust=True)
if isinstance(hist_raw.columns, pd.MultiIndex): hist_raw.columns = hist_raw.columns.get_level_values(0)
hist_6m = hist_raw.tail(126)
hist_3m = hist_raw.tail(63)
info = yf.Ticker('BBCA.JK').info

from indicators.rsi import calculate_rsi
from indicators.macd_bb import calculate_macd_bb
from indicators.adx import calculate_adx
from indicators.stochastic import calculate_stochastic
from indicators.obv import calculate_obv
from indicators.mfi import calculate_mfi
from indicators.williams_r import calculate_williams_r
from indicators.composite import calculate_composite

r = calculate_composite(
    info, None, None,
    calculate_macd_bb(hist_6m), calculate_rsi(hist_6m),
    None, None, None, hist_raw,
    adx_data=calculate_adx(hist_3m),
    stoch_data=calculate_stochastic(hist_3m),
    obv_data=calculate_obv(hist_raw),
    mfi_data=calculate_mfi(hist_3m),
    willr_data=calculate_williams_r(hist_3m),
)
print(r)
assert r is not None
assert 0 <= r['final'] <= 100
assert r['signal'] in ('STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL')
print('Composite OK')
"
```

- [ ] **Step 3: Commit**

```bash
git add indicators/composite.py
git commit -m "feat: fix composite technical score to use all 8 indicators, update weights"
```

---

## Task 6: ATR-Based Stop Loss in Outlook

**Files:**
- Modify: `indicators/key_levels.py`

Change `calculate_outlook` signature from `(key_levels, composite)` to `(key_levels, composite, atr=None)`.

- [ ] **Step 1: Update `calculate_outlook` in `indicators/key_levels.py`**

Find the line:
```python
def calculate_outlook(key_levels, composite):
```

Replace with:
```python
def calculate_outlook(key_levels, composite, atr=None):
```

Then find the block that computes `stop_loss` and `sl_pct`. It currently looks like:
```python
        entry_mid = (entry_low + entry_high) / 2
        sl_pct = abs((entry_mid - stop_loss) / entry_mid * 100) if entry_mid else 0
```

Replace the stop_loss + sl_pct computation section with:
```python
        entry_mid = (entry_low + entry_high) / 2

        # ATR-based stop loss overrides pivot-based when available
        if atr and atr.get('value') and entry_mid:
            stop_loss = round(entry_mid - 2 * atr['value'], 0)
            sl_pct    = round(2 * atr['pct'], 1)
        else:
            sl_pct = abs((entry_mid - stop_loss) / entry_mid * 100) if entry_mid else 0
```

- [ ] **Step 2: Verify outlook still works with and without ATR**

```bash
cd /Users/fadhel/Documents/projects/MyTrading/idx-analyzer && python3 -c "
import yfinance as yf, pandas as pd, warnings; warnings.filterwarnings('ignore')
hist = yf.download('BBCA.JK', period='3mo', interval='1d', progress=False, auto_adjust=True)
if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
from indicators.key_levels import calculate_key_levels, calculate_outlook
from indicators.atr import calculate_atr
kl  = calculate_key_levels(hist)
atr = calculate_atr(hist)
ol_with    = calculate_outlook(kl, None, atr=atr)
ol_without = calculate_outlook(kl, None)
print('With ATR stop loss:', ol_with['stop_loss'], '| sl_pct:', ol_with['sl_pct'])
print('Without ATR stop loss:', ol_without['stop_loss'], '| sl_pct:', ol_without['sl_pct'])
assert ol_with is not None and ol_without is not None
print('Outlook OK')
"
```

- [ ] **Step 3: Commit**

```bash
git add indicators/key_levels.py
git commit -m "feat: use ATR-based stop loss in calculate_outlook, fallback to pivot-based"
```

---

## Task 7: Wire Up in app.py

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add imports at top of `app.py`**

After the existing imports block, add:
```python
from indicators.atr import calculate_atr
from indicators.mfi import calculate_mfi
from indicators.williams_r import calculate_williams_r
from indicators.fundamental import calculate_dividend_yield, calculate_ev_ebitda
```

- [ ] **Step 2: Add new indicator calculations in `analyze()`**

After the line `stochastic = calculate_stochastic(data['hist_3m'])`, add:
```python
        atr        = calculate_atr(data['hist_6m'])
        mfi        = calculate_mfi(data['hist_3m'])
        williams_r = calculate_williams_r(data['hist_3m'])
        div_yield  = calculate_dividend_yield(info)
        ev_ebitda  = calculate_ev_ebitda(info)
```

- [ ] **Step 3: Update `calculate_composite` call**

Replace:
```python
        composite = calculate_composite(
            info, piotroski, altman, macd_bb, rsi,
            sharpe, sortino, rvol, data['hist_1y']
        )
```

With:
```python
        composite = calculate_composite(
            info, piotroski, altman, macd_bb, rsi,
            sharpe, sortino, rvol, data['hist_1y'],
            adx_data=adx, stoch_data=stochastic, obv_data=obv,
            mfi_data=mfi, willr_data=williams_r,
        )
```

- [ ] **Step 4: Update `calculate_outlook` call**

Replace:
```python
        outlook = calculate_outlook(key_levels, composite)
```

With:
```python
        outlook = calculate_outlook(key_levels, composite, atr=atr)
```

- [ ] **Step 5: Add new fields to the `return jsonify(...)` dict**

Inside the `clean_nan({...})` dict, add after `"obv": obv,`:
```python
            "atr":        atr,
            "mfi":        mfi,
            "williams_r": williams_r,
            "div_yield":  div_yield,
            "ev_ebitda":  ev_ebitda,
```

- [ ] **Step 6: Smoke test the API**

```bash
cd /Users/fadhel/Documents/projects/MyTrading/idx-analyzer && python3 -c "
import app as a, json
with a.app.test_client() as c:
    r = c.get('/api/analyze?ticker=BBCA.JK')
    d = r.get_json()
    assert 'atr' in d, 'atr missing'
    assert 'mfi' in d, 'mfi missing'
    assert 'williams_r' in d, 'williams_r missing'
    assert 'div_yield' in d, 'div_yield missing'
    assert 'ev_ebitda' in d, 'ev_ebitda missing'
    assert d['composite'] is not None
    print('ATR:', d['atr'])
    print('MFI:', d['mfi'])
    print('Williams R:', d['williams_r'])
    print('Composite:', d['composite']['final'], d['composite']['signal'])
    print('API wiring OK')
"
```

- [ ] **Step 7: Commit**

```bash
git add app.py
git commit -m "feat: wire ATR, MFI, Williams %R, EV/EBITDA into app.py"
```

---

## Task 8: UI — Technical Grid Cards

**Files:**
- Modify: `static/app.js`

### 8a — Update `renderTechnical` signature and add 3 new cards

- [ ] **Step 1: Update function signature (line 385)**

Replace:
```javascript
function renderTechnical(mb, rsi, sma, rvol, adx, avwap, stoch, obv) {
  if (!mb && !rsi && !sma && !rvol && !adx && !avwap && !stoch && !obv) return '<p class="no-data">Data historis tidak cukup.</p>';
```

With:
```javascript
function renderTechnical(mb, rsi, sma, rvol, adx, avwap, stoch, obv, atr, mfi, willr) {
  if (!mb && !rsi && !sma && !rvol && !adx && !avwap && !stoch && !obv && !atr && !mfi && !willr) return '<p class="no-data">Data historis tidak cukup.</p>';
```

- [ ] **Step 2: Add ATR card after the OBV card (after line ~537, before `return '<div class="tech-grid">'`)**

Add before the `return` line:
```javascript
  // 10. ATR
  if (atr) {
    var atrColor = atr.signal === 'HIGH' ? 'var(--warn)' : atr.signal === 'LOW' ? 'var(--info)' : 'var(--pos)';
    var atrBadge = atr.signal === 'HIGH' ? 'br' : atr.signal === 'LOW' ? 'bb' : 'by';
    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">ATR (14) <span style="font-size:9px;opacity:.6;">Volatility</span></div>' +
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">' +
        '<span class="badge ' + atrBadge + '">' + atr.signal + '</span>' +
      '</div>' +
      '<div class="tech-row"><span class="tech-row-label">ATR Value</span><span style="color:' + atrColor + ';">Rp ' + (atr.value != null ? atr.value.toLocaleString('id') : '—') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">ATR %</span><span style="color:' + atrColor + ';">' + (atr.pct != null ? atr.pct + '%' : '—') + '</span></div>' +
    '</div>');
  }

  // 11. MFI
  if (mfi) {
    var mfiColor = mfi.value > 80 ? 'var(--warn)' : mfi.value < 20 ? 'var(--info)' : 'var(--pos)';
    var mfiSigCls = mfi.signal === 'OVERBOUGHT' ? 'sig-overbought' : mfi.signal === 'OVERSOLD' ? 'sig-oversold' : 'sig-netral';
    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">MFI (14) <span style="font-size:9px;opacity:.6;">Money Flow Index</span></div>' +
      '<div class="tech-sig ' + mfiSigCls + '">' + mfi.signal + '</div>' +
      '<div style="font-family:\'JetBrains Mono\',monospace;font-size:28px;font-weight:600;color:' + mfiColor + ';margin:6px 0;">' + mfi.value + '</div>' +
      '<div style="margin:10px 0;">' +
        '<div style="height:8px;border-radius:4px;overflow:hidden;background:rgba(255,255,255,0.04);">' +
          '<div style="height:100%;border-radius:4px;width:' + mfi.value + '%;background:' + mfiColor + ';transition:width .5s;"></div>' +
        '</div>' +
        '<div style="display:flex;justify-content:space-between;font-family:\'JetBrains Mono\',monospace;font-size:8px;color:var(--text-secondary);margin-top:3px;">' +
          '<span style="color:var(--info);">0</span><span>20</span><span>50</span><span>80</span><span style="color:var(--warn);">100</span>' +
        '</div>' +
      '</div>' +
    '</div>');
  }

  // 12. Williams %R
  if (willr) {
    var wrColor = willr.value > -20 ? 'var(--warn)' : willr.value < -80 ? 'var(--info)' : 'var(--pos)';
    var wrSigCls = willr.signal === 'OVERBOUGHT' ? 'sig-overbought' : willr.signal === 'OVERSOLD' ? 'sig-oversold' : 'sig-netral';
    var wrBarW = Math.abs(willr.value);
    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">Williams %R (14)</div>' +
      '<div class="tech-sig ' + wrSigCls + '">' + willr.signal + '</div>' +
      '<div style="font-family:\'JetBrains Mono\',monospace;font-size:28px;font-weight:600;color:' + wrColor + ';margin:6px 0;">' + willr.value + '</div>' +
      '<div style="margin:10px 0;">' +
        '<div style="height:8px;border-radius:4px;overflow:hidden;background:rgba(255,255,255,0.04);">' +
          '<div style="height:100%;border-radius:4px;width:' + wrBarW + '%;background:' + wrColor + ';transition:width .5s;"></div>' +
        '</div>' +
        '<div style="display:flex;justify-content:space-between;font-family:\'JetBrains Mono\',monospace;font-size:8px;color:var(--text-secondary);margin-top:3px;">' +
          '<span style="color:var(--warn);">-100</span><span>-80</span><span>-50</span><span>-20</span><span style="color:var(--info);">0</span>' +
        '</div>' +
      '</div>' +
    '</div>');
  }
```

### 8b — Update `render()` call to `renderTechnical`

- [ ] **Step 3: Update renderTechnical call in `render()` (line ~894)**

Replace:
```javascript
  html += sec('', 'TECHNICAL INDICATORS', renderTechnical(d.macd_bb, d.rsi, d.sma, d.rvol, d.adx, d.avwap, d.stochastic, d.obv), true);
```

With:
```javascript
  html += sec('', 'TECHNICAL INDICATORS', renderTechnical(d.macd_bb, d.rsi, d.sma, d.rvol, d.adx, d.avwap, d.stochastic, d.obv, d.atr, d.mfi, d.williams_r), true);
```

### 8c — Update composite weights display

- [ ] **Step 4: Update weights in `renderComposite` (line ~293)**

Replace:
```javascript
  var weights = { Fundamental: '30%', Technical: '25%', Risk: '20%', Momentum: '15%', Sentiment: '10%' };
```

With:
```javascript
  var weights = { Fundamental: '28%', Technical: '32%', Risk: '20%', Momentum: '13%', Sentiment: '7%' };
```

### 8d — Add MFI and Williams %R to Signal Strip

- [ ] **Step 5: Add MFI and Williams %R votes in `renderSignalStrip` (after the OBV block ~line 831)**

After the `if (d.obv) { ... votes.push(...) }` block, add:
```javascript
  if (d.mfi) {
    var mfiv = d.mfi.signal === 'OVERSOLD' ? 1 : d.mfi.signal === 'OVERBOUGHT' ? -1 : 0;
    votes.push({ name: 'MFI', v: mfiv, label: String(d.mfi.value) });
  }
  if (d.williams_r) {
    var wrv = d.williams_r.signal === 'OVERSOLD' ? 1 : d.williams_r.signal === 'OVERBOUGHT' ? -1 : 0;
    votes.push({ name: 'W%R', v: wrv, label: String(d.williams_r.value) });
  }
```

### 8e — Add MFI and Williams %R to Technical Consensus

- [ ] **Step 6: Add MFI and Williams %R votes in `renderConsensus` (after the OBV block ~line 346)**

After the `if (d.rvol) { ... votes.push(...) }` block in `renderConsensus`, add:
```javascript
  if (d.mfi) {
    var mficv = d.mfi.signal === 'OVERSOLD' ? 1 : d.mfi.signal === 'OVERBOUGHT' ? -1 : 0;
    var mficls = d.mfi.signal === 'OVERSOLD' ? 'sig-oversold' : d.mfi.signal === 'OVERBOUGHT' ? 'sig-overbought' : 'sig-netral';
    votes.push({ name: 'MFI (14)', label: d.mfi.signal, cls: mficls, vote: mficv, detail: 'MFI ' + d.mfi.value });
  }
  if (d.williams_r) {
    var wrcv = d.williams_r.signal === 'OVERSOLD' ? 1 : d.williams_r.signal === 'OVERBOUGHT' ? -1 : 0;
    var wrcls = d.williams_r.signal === 'OVERSOLD' ? 'sig-oversold' : d.williams_r.signal === 'OVERBOUGHT' ? 'sig-overbought' : 'sig-netral';
    votes.push({ name: 'Williams %R (14)', label: d.williams_r.signal, cls: wrcls, vote: wrcv, detail: 'W%R ' + d.williams_r.value });
  }
```

### 8f — Add EV/EBITDA to Key Metrics

- [ ] **Step 7: Update `renderMetrics` to show EV/EBITDA (line ~272)**

In `renderMetrics`, find the `right` array and add EV/EBITDA after Div. Yield:

Replace:
```javascript
  var right = [
    ['P/E Ratio', fval(i.trailingPE)],
    ['Debt/Equity', fval(i.debtToEquity)],
    ['ROE', fval(i.returnOnEquity)],
    ['Current Ratio', fval(i.currentRatio)],
    ['Div. Yield', i.dividendYield != null ? (i.dividendYield * 100).toFixed(2) + '%' : '<span class="na">—</span>'],
    ['Target Upside', upside != null ? '<span class="' + (upside > 0 ? 'pos' : 'neg') + '">' + (upside > 0 ? '+' : '') + upside + '%</span>' : '<span class="na">—</span>']
  ];
```

With:
```javascript
  var evLabel = (d.ev_ebitda && d.ev_ebitda.value != null)
    ? d.ev_ebitda.value + 'x <span style="opacity:.6;font-size:10px;">' + d.ev_ebitda.signal + '</span>'
    : '<span class="na">—</span>';
  var right = [
    ['P/E Ratio', fval(i.trailingPE)],
    ['Debt/Equity', fval(i.debtToEquity)],
    ['ROE', fval(i.returnOnEquity)],
    ['Current Ratio', fval(i.currentRatio)],
    ['Div. Yield', i.dividendYield != null ? (i.dividendYield * 100).toFixed(2) + '%' : '<span class="na">—</span>'],
    ['EV/EBITDA', evLabel],
    ['Target Upside', upside != null ? '<span class="' + (upside > 0 ? 'pos' : 'neg') + '">' + (upside > 0 ? '+' : '') + upside + '%</span>' : '<span class="na">—</span>']
  ];
```

Note: `renderMetrics(d)` receives `d` (full data), so the function signature must be updated too. Find `function renderMetrics(d)` — it already receives `d`, so `d.ev_ebitda` is accessible. No signature change needed.

- [ ] **Step 8: Commit**

```bash
git add static/app.js
git commit -m "feat: add ATR, MFI, Williams %R cards to technical grid; update composite weights display; add EV/EBITDA to key metrics"
```

---

## Task 9: Final Push

- [ ] **Step 1: Run full smoke test**

```bash
cd /Users/fadhel/Documents/projects/MyTrading/idx-analyzer && python3 -c "
import app as a
with a.app.test_client() as c:
    r = c.get('/api/analyze?ticker=BBCA.JK')
    d = r.get_json()
    required = ['atr','mfi','williams_r','div_yield','ev_ebitda','composite','outlook']
    for k in required:
        assert k in d, f'{k} missing from response'
    assert d['composite']['final'] is not None
    assert d['outlook']['stop_loss'] is not None
    print('All fields present. Composite:', d['composite']['final'], d['composite']['signal'])
    print('Outlook stop loss:', d['outlook']['stop_loss'], '±', d['outlook']['sl_pct'], '%')
    print('Full smoke test PASSED')
"
```

- [ ] **Step 2: Push all commits**

```bash
git push origin main
```
