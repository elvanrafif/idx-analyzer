# IDX Analyzer Rework — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Perombakan total IDX Analyzer — modular architecture, glassmorphism UI, AI integration, calculation fixes.

**Architecture:** Pecah monolith `app.py` (1116 baris) jadi modular structure (services/, indicators/, templates/, static/). Centralized data fetching via `yahoo_fetcher.py`. AI analysis via GLM4.1 Air. Glassmorphism dark-mode UI dengan tabbed sections.

**Tech Stack:** Python 3.11, Flask 3.0, yfinance, pandas, numpy, OpenAI SDK (for GLM4.1 Air), Gunicorn

---

## File Structure Map

| File | Responsibility |
|------|---------------|
| `app.py` | Flask routes, orchestrator — slim, only routes |
| `services/yahoo_fetcher.py` | Fetch all yfinance data in one pass, return structured dict |
| `services/ai_analyzer.py` | Call GLM4.1 Air API per section, return insight text |
| `indicators/piotroski.py` | Piotroski F-Score with avg-assets ROA fix |
| `indicators/altman_z.py` | Altman Z-Score (unchanged logic, modularized) |
| `indicators/macd_bb.py` | MACD + Bollinger Bands with bandwidth + improved cross |
| `indicators/rsi.py` | RSI with Wilder's Smoothing |
| `indicators/sma.py` | EMA20, SMA50, SMA200 + Golden/Death Cross |
| `indicators/rvol.py` | Relative Volume vs 20d avg |
| `indicators/risk_metrics.py` | Sharpe, Sortino, FCF Yield with configurable risk-free rate |
| `indicators/composite.py` | Composite Score 0-100, accepts pre-computed indicators |
| `templates/index.html` | Main HTML page (glassmorphism) |
| `static/style.css` | All CSS (glassmorphism dark/light) |
| `static/app.js` | Frontend JS (fetch, render, tabs, AI insight) |
| `.env` | GLM_API_KEY, RISK_FREE_RATE |

---

### Task 1: Project Structure + Dependencies

**Files:**
- Create: `services/__init__.py`
- Create: `indicators/__init__.py`
- Create: `.env`
- Create: `.gitignore`
- Modify: `requirements.txt`
- Modify: `Dockerfile`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p services indicators templates static
touch services/__init__.py indicators/__init__.py
```

- [ ] **Step 2: Update requirements.txt**

Write to `requirements.txt`:
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

- [ ] **Step 3: Create .env file**

Write to `.env`:
```
GLM_API_KEY=your_api_key_here
RISK_FREE_RATE=0.065
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

- [ ] **Step 4: Update .gitignore**

Append to `.gitignore`:
```
.env
__pycache__/
.superpowers/
```

- [ ] **Step 5: Update Dockerfile**

Write to `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]
```

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "chore: setup modular project structure and dependencies"
```

---

### Task 2: Yahoo Fetcher Service

**Files:**
- Create: `services/yahoo_fetcher.py`

This is the centralized data fetcher. It calls yfinance ONCE per ticker and distributes data to all indicators.

- [ ] **Step 1: Write services/yahoo_fetcher.py**

```python
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone


def fetch_ticker_data(ticker):
    stock = yf.Ticker(f"{ticker}.JK")
    info = stock.info

    if not info or not (info.get('regularMarketPrice') or info.get('currentPrice')):
        return None

    clean_info = {
        k: (None if isinstance(v, float) and pd.isna(v) else v)
        for k, v in info.items()
    }

    hist_6m = stock.history(period='6mo')
    hist_1y = stock.history(period='1y')
    hist_3m = stock.history(period='3mo')

    balance_sheet = stock.balance_sheet
    financials = stock.financials
    cashflow = stock.cashflow
    quarterly = stock.quarterly_financials

    return {
        'ticker': ticker,
        'info': clean_info,
        'hist_6m': hist_6m,
        'hist_1y': hist_1y,
        'hist_3m': hist_3m,
        'balance_sheet': balance_sheet,
        'financials': financials,
        'cashflow': cashflow,
        'quarterly': quarterly,
        'updated': datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M WIB"),
    }


def df_to_dict(df):
    if df is None or df.empty:
        return None
    try:
        cols = [
            f"Q{c.quarter} {c.year}" if hasattr(c, 'quarter') else str(c.year)
            for c in df.columns[:4]
        ]
        data = {}
        for idx in df.index:
            row = {}
            for j, col in enumerate(df.columns[:4]):
                try:
                    v = df.loc[idx, col]
                    row[cols[j]] = None if pd.isna(v) else float(v)
                except:
                    row[cols[j]] = None
            data[str(idx)] = row
        return {"columns": cols, "data": data}
    except:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add services/yahoo_fetcher.py && git commit -m "feat: add centralized yahoo data fetcher service"
```

---

### Task 3: RSI Indicator (Wilder's Smoothing Fix)

**Files:**
- Create: `indicators/rsi.py`

- [ ] **Step 1: Write indicators/rsi.py**

```python
import pandas as pd


def calculate_rsi(hist_3m):
    if hist_3m is None or len(hist_3m) < 15:
        return None
    try:
        close = hist_3m['Close']
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta.clip(upper=0))
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        val = round(float(rsi.iloc[-1]), 1)
        signal = 'OVERBOUGHT' if val > 70 else 'OVERSOLD' if val < 30 else 'NEUTRAL'
        return {'value': val, 'signal': signal}
    except:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add indicators/rsi.py && git commit -m "feat: add RSI indicator with Wilder's smoothing"
```

---

### Task 4: MACD + Bollinger Bands (Bandwidth + Improved Cross)

**Files:**
- Create: `indicators/macd_bb.py`

- [ ] **Step 1: Write indicators/macd_bb.py**

```python
import pandas as pd


def calculate_macd_bb(hist_6m):
    if hist_6m is None or len(hist_6m) < 30:
        return None
    try:
        close = hist_6m['Close']

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        sig = macd.ewm(span=9, adjust=False).mean()
        hst = macd - sig

        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        upper = sma20 + 2 * std20
        lower = sma20 - 2 * std20

        cp = float(close.iloc[-1])
        cm = float(macd.iloc[-1])
        cs = float(sig.iloc[-1])
        ch = float(hst.iloc[-1])
        ph = float(hst.iloc[-2])
        cu = float(upper.iloc[-1])
        cl = float(lower.iloc[-1])
        csma = float(sma20.iloc[-1])

        bb_pct = (cp - cl) / (cu - cl) if (cu - cl) != 0 else 0.5
        bandwidth = round((cu - cl) / csma, 4) if csma != 0 else 0
        squeeze = bandwidth < 0.03

        msig = 'BULLISH' if cm > cs else 'BEARISH'
        threshold = cp * 0.001
        cross = None
        if ch > 0 and ph <= 0 and abs(ch) > threshold:
            cross = 'GOLDEN CROSS'
        elif ch < 0 and ph >= 0 and abs(ch) > threshold:
            cross = 'DEATH CROSS'

        bsig = 'OVERBOUGHT' if cp > cu else 'OVERSOLD' if cp < cl else ('BULLISH' if cp > csma else 'BEARISH')

        return {
            'macd': {
                'line': round(cm, 2),
                'signal': round(cs, 2),
                'hist': round(ch, 2),
                'signal_label': msig,
                'cross': cross,
            },
            'bb': {
                'upper': round(cu, 0),
                'mid': round(csma, 0),
                'lower': round(cl, 0),
                'pct_b': round(bb_pct, 2),
                'bandwidth': bandwidth,
                'squeeze': squeeze,
                'signal': bsig,
            },
        }
    except:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add indicators/macd_bb.py && git commit -m "feat: add MACD+BB indicator with bandwidth and improved cross detection"
```

---

### Task 5: SMA Indicator

**Files:**
- Create: `indicators/sma.py`

- [ ] **Step 1: Write indicators/sma.py**

```python
def calculate_sma(hist_1y):
    if hist_1y is None or len(hist_1y) < 50:
        return None
    try:
        close = hist_1y['Close']
        price = round(float(close.iloc[-1]), 0)
        ema20 = round(float(close.ewm(span=20, adjust=False).mean().iloc[-1]), 0)
        sma50 = round(float(close.rolling(50).mean().iloc[-1]), 0)
        sma200 = round(float(close.rolling(200).mean().iloc[-1]), 0) if len(close) >= 200 else None
        golden_cross = bool(sma50 > sma200) if sma200 else None
        return {
            'price': price,
            'ema20': ema20,
            'sma50': sma50,
            'sma200': sma200,
            'above_sma50': price > sma50,
            'golden_cross': golden_cross,
        }
    except:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add indicators/sma.py && git commit -m "feat: add SMA/EMA indicator module"
```

---

### Task 6: Piotroski F-Score (Avg Assets ROA Fix)

**Files:**
- Create: `indicators/piotroski.py`

- [ ] **Step 1: Write indicators/piotroski.py**

```python
import pandas as pd


def _get_value(df, col_idx, *keys):
    if df is None or col_idx >= len(df.columns):
        return None
    col = df.columns[col_idx]
    for key in keys:
        for idx in df.index:
            if key.lower() in str(idx).lower():
                try:
                    v = df.loc[idx, col]
                    return None if pd.isna(v) else float(v)
                except:
                    pass
    return None


def calculate_piotroski(balance_sheet, financials, cashflow):
    if balance_sheet is None or balance_sheet.empty:
        return None
    if financials is None or financials.empty:
        return None
    if cashflow is None or cashflow.empty:
        return None
    if len(balance_sheet.columns) < 2 or len(financials.columns) < 2:
        return None

    try:
        bs, fs, cf = balance_sheet, financials, cashflow

        ta0 = _get_value(bs, 0, 'total assets')
        ta1 = _get_value(bs, 1, 'total assets')
        ni0 = _get_value(fs, 0, 'net income')
        ni1 = _get_value(fs, 1, 'net income')
        ocf0 = _get_value(cf, 0, 'operating cash flow')
        ltd0 = _get_value(bs, 0, 'long term debt')
        ltd1 = _get_value(bs, 1, 'long term debt')
        ca0 = _get_value(bs, 0, 'current assets')
        cl0 = _get_value(bs, 0, 'current liabilities')
        ca1 = _get_value(bs, 1, 'current assets')
        cl1 = _get_value(bs, 1, 'current liabilities')
        sh0 = _get_value(bs, 0, 'ordinary shares', 'common stock')
        sh1 = _get_value(bs, 1, 'ordinary shares', 'common stock')
        gp0 = _get_value(fs, 0, 'gross profit')
        rev0 = _get_value(fs, 0, 'total revenue')
        gp1 = _get_value(fs, 1, 'gross profit')
        rev1 = _get_value(fs, 1, 'total revenue')

        avg_ta0 = (ta0 + ta1) / 2 if ta0 and ta1 else ta0
        avg_ta1 = None
        ta2 = _get_value(bs, 2, 'total assets')
        if ta1 and ta2:
            avg_ta1 = (ta1 + ta2) / 2
        elif ta1:
            avg_ta1 = ta1

        score = 0
        details = {}

        roa0 = ni0 / avg_ta0 if ni0 and avg_ta0 else None
        roa1 = ni1 / avg_ta1 if ni1 and avg_ta1 else None

        f1 = 1 if roa0 and roa0 > 0 else 0
        score += f1
        details['F1'] = {'label': 'ROA Positif', 'pass': bool(f1),
                         'value': f'{roa0*100:.1f}%' if roa0 else '—'}

        f2 = 1 if ocf0 and ocf0 > 0 else 0
        score += f2
        details['F2'] = {'label': 'Arus Kas Operasi > 0', 'pass': bool(f2),
                         'value': f'Rp {ocf0/1e9:.1f}M' if ocf0 else '—'}

        f3 = 1 if roa0 and roa1 and roa0 > roa1 else 0
        score += f3
        details['F3'] = {'label': 'ROA Meningkat YoY', 'pass': bool(f3),
                         'value': f'{roa0*100:.1f}% vs {roa1*100:.1f}%' if (roa0 and roa1) else '—'}

        ocf_ta = ocf0 / ta0 if ocf0 and ta0 else None
        f4 = 1 if ocf_ta and roa0 and ocf_ta > roa0 else 0
        score += f4
        details['F4'] = {'label': 'Kualitas Laba (OCF>NI)', 'pass': bool(f4),
                         'value': f'{ocf_ta*100:.1f}% vs {roa0*100:.1f}%' if (ocf_ta and roa0) else '—'}

        lev0 = ltd0 / ta0 if ltd0 is not None and ta0 else None
        lev1 = ltd1 / ta1 if ltd1 is not None and ta1 else None
        f5 = 1 if lev0 is not None and lev1 is not None and lev0 <= lev1 else 0
        score += f5
        details['F5'] = {'label': 'Leverage Tidak Naik', 'pass': bool(f5),
                         'value': f'{lev0*100:.1f}% vs {lev1*100:.1f}%' if (lev0 is not None and lev1 is not None) else '—'}

        cr0 = ca0 / cl0 if ca0 and cl0 else None
        cr1 = ca1 / cl1 if ca1 and cl1 else None
        f6 = 1 if cr0 and cr1 and cr0 >= cr1 else 0
        score += f6
        details['F6'] = {'label': 'Current Ratio Tidak Turun', 'pass': bool(f6),
                         'value': f'{cr0:.2f} vs {cr1:.2f}' if (cr0 and cr1) else '—'}

        f7 = 1 if sh0 and sh1 and sh0 <= sh1 * 1.02 else 0
        score += f7
        details['F7'] = {'label': 'Tidak Ada Dilusi Saham', 'pass': bool(f7),
                         'value': f'{sh0/1e9:.2f}B vs {sh1/1e9:.2f}B' if (sh0 and sh1) else '—'}

        gm0 = gp0 / rev0 if gp0 and rev0 else None
        gm1 = gp1 / rev1 if gp1 and rev1 else None
        f8 = 1 if gm0 and gm1 and gm0 >= gm1 else 0
        score += f8
        details['F8'] = {'label': 'Gross Margin Tidak Turun', 'pass': bool(f8),
                         'value': f'{gm0*100:.1f}% vs {gm1*100:.1f}%' if (gm0 and gm1) else '—'}

        at0 = rev0 / ta0 if rev0 and ta0 else None
        at1 = rev1 / ta1 if rev1 and ta1 else None
        f9 = 1 if at0 and at1 and at0 >= at1 else 0
        score += f9
        details['F9'] = {'label': 'Asset Turnover Tidak Turun', 'pass': bool(f9),
                         'value': f'{at0:.2f}x vs {at1:.2f}x' if (at0 and at1) else '—'}

        prev_score = None
        if len(bs.columns) >= 3 and len(fs.columns) >= 3:
            try:
                prev_score = _quick_piotroski(bs, fs, cf)
            except:
                pass

        trend = None
        if prev_score is not None:
            trend = 'NAIK' if score > prev_score else 'TURUN' if score < prev_score else 'STABIL'

        rating = 'KUAT' if score >= 7 else 'CUKUP' if score >= 5 else 'LEMAH'
        return {
            'score': score,
            'max': 9,
            'rating': rating,
            'trend': trend,
            'details': details,
        }
    except:
        return None


def _quick_piotroski(bs, fs, cf):
    ta0 = _get_value(bs, 1, 'total assets')
    ta1 = _get_value(bs, 2, 'total assets')
    ni0 = _get_value(fs, 1, 'net income')
    ocf0 = _get_value(cf, 1, 'operating cash flow') if len(cf.columns) >= 2 else None
    if not ta0 or not ni0:
        return None
    avg_ta = (ta0 + ta1) / 2 if ta0 and ta1 else ta0
    s = 0
    roa = ni0 / avg_ta if avg_ta else None
    if roa and roa > 0: s += 1
    if ocf0 and ocf0 > 0: s += 1
    if roa: s += 1
    ocf_ta = ocf0 / ta0 if ocf0 and ta0 else None
    if ocf_ta and roa and ocf_ta > roa: s += 1
    ltd0 = _get_value(bs, 1, 'long term debt')
    ltd1 = _get_value(bs, 2, 'long term debt')
    lev0 = ltd0 / ta0 if ltd0 is not None and ta0 else None
    lev1 = ltd1 / ta1 if ltd1 is not None and ta1 else None
    if lev0 is not None and lev1 is not None and lev0 <= lev1: s += 1
    ca0 = _get_value(bs, 1, 'current assets')
    cl0 = _get_value(bs, 1, 'current liabilities')
    ca1 = _get_value(bs, 2, 'current assets')
    cl1 = _get_value(bs, 2, 'current liabilities')
    cr0 = ca0 / cl0 if ca0 and cl0 else None
    cr1 = ca1 / cl1 if ca1 and cl1 else None
    if cr0 and cr1 and cr0 >= cr1: s += 1
    sh0 = _get_value(bs, 1, 'ordinary shares', 'common stock')
    sh1 = _get_value(bs, 2, 'ordinary shares', 'common stock')
    if sh0 and sh1 and sh0 <= sh1 * 1.02: s += 1
    gp0 = _get_value(fs, 1, 'gross profit')
    rev0 = _get_value(fs, 1, 'total revenue')
    gp1 = _get_value(fs, 2, 'gross profit')
    rev1 = _get_value(fs, 2, 'total revenue')
    gm0 = gp0 / rev0 if gp0 and rev0 else None
    gm1 = gp1 / rev1 if gp1 and rev1 else None
    if gm0 and gm1 and gm0 >= gm1: s += 1
    at0 = rev0 / ta0 if rev0 and ta0 else None
    at1 = rev1 / ta1 if rev1 and ta1 else None
    if at0 and at1 and at0 >= at1: s += 1
    return s
```

- [ ] **Step 2: Commit**

```bash
git add indicators/piotroski.py && git commit -m "feat: add Piotroski F-Score with avg-assets ROA and trend"
```

---

### Task 7: Altman Z-Score

**Files:**
- Create: `indicators/altman_z.py`

- [ ] **Step 1: Write indicators/altman_z.py**

```python
import pandas as pd


def _bsv(bs, *keys):
    col = bs.columns[0]
    for key in keys:
        for idx in bs.index:
            if key.lower() in str(idx).lower():
                try:
                    v = bs.loc[idx, col]
                    return None if pd.isna(v) else float(v)
                except:
                    pass
    return None


def _fsv(fs, *keys):
    col = fs.columns[0]
    for key in keys:
        for idx in fs.index:
            if key.lower() in str(idx).lower():
                try:
                    v = fs.loc[idx, col]
                    return None if pd.isna(v) else float(v)
                except:
                    pass
    return None


def calculate_altman_z(balance_sheet, financials):
    if balance_sheet is None or balance_sheet.empty:
        return None
    if financials is None or financials.empty:
        return None
    try:
        bs, fs = balance_sheet, financials
        ta = _bsv(bs, 'total assets')
        ca = _bsv(bs, 'current assets')
        cl = _bsv(bs, 'current liabilities')
        re = _bsv(bs, 'retained earnings')
        te = _bsv(bs, 'stockholders equity', 'total equity')
        tl = _bsv(bs, 'total liabilities')
        ebit = _fsv(fs, 'operating income', 'ebit')
        if not all([ta, ca, cl, te, tl]) or ta == 0 or tl == 0:
            return None

        X1 = (ca - cl) / ta
        X2 = (re or 0) / ta
        X3 = (ebit or 0) / ta
        X4 = te / tl
        z = 6.56 * X1 + 3.26 * X2 + 6.72 * X3 + 1.05 * X4
        zone = 'AMAN' if z > 2.6 else 'WASPADA' if z > 1.1 else 'BAHAYA'
        descs = {
            'AMAN': 'Risiko kebangkrutan rendah',
            'WASPADA': 'Grey zone — perlu monitoring',
            'BAHAYA': 'Risiko kebangkrutan tinggi',
        }
        return {
            'z_score': round(z, 2),
            'zone': zone,
            'desc': descs[zone],
            'components': {
                'X1 (Working Capital/TA)': round(X1, 3),
                'X2 (Retained Earn/TA)': round(X2, 3),
                'X3 (EBIT/TA)': round(X3, 3),
                'X4 (Equity/Liab)': round(X4, 3),
            },
        }
    except:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add indicators/altman_z.py && git commit -m "feat: add Altman Z-Score indicator module"
```

---

### Task 8: Relative Volume

**Files:**
- Create: `indicators/rvol.py`

- [ ] **Step 1: Write indicators/rvol.py**

```python
def calculate_rvol(hist_3m):
    if hist_3m is None or len(hist_3m) < 21:
        return None
    try:
        avg = float(hist_3m['Volume'].iloc[:-1].tail(20).mean())
        today = float(hist_3m['Volume'].iloc[-1])
        if avg == 0:
            return None
        rvol = today / avg
        sig = 'SANGAT TINGGI' if rvol > 3 else 'TINGGI' if rvol > 2 else 'NORMAL' if rvol > 0.7 else 'RENDAH'
        return {'rvol': round(rvol, 2), 'today': int(today), 'avg': int(avg), 'signal': sig}
    except:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add indicators/rvol.py && git commit -m "feat: add relative volume indicator module"
```

---

### Task 9: Risk Metrics (Sharpe, Sortino, FCF Yield)

**Files:**
- Create: `indicators/risk_metrics.py`

- [ ] **Step 1: Write indicators/risk_metrics.py**

```python
import numpy as np
import os


def get_risk_free_rate():
    try:
        return float(os.environ.get('RISK_FREE_RATE', '0.065'))
    except:
        return 0.065


def calculate_sharpe(hist_1y):
    if hist_1y is None or len(hist_1y) < 20:
        return None
    try:
        close = hist_1y['Close']
        ret = close.pct_change().dropna()
        if len(ret) == 0:
            return None
        ann_ret = ret.mean() * 252
        ann_std = ret.std() * np.sqrt(252)
        rf = get_risk_free_rate()
        return round((ann_ret - rf) / ann_std, 3) if ann_std else None
    except:
        return None


def calculate_sortino(hist_1y):
    if hist_1y is None or len(hist_1y) < 20:
        return None
    try:
        close = hist_1y['Close']
        ret = close.pct_change().dropna()
        if len(ret) == 0:
            return None
        ann_ret = ret.mean() * 252
        down = ret[ret < 0]
        down_std = down.std() * np.sqrt(252) if len(down) > 0 else 0
        rf = get_risk_free_rate()
        return round((ann_ret - rf) / down_std, 3) if down_std else None
    except:
        return None


def calculate_fcf_yield(info):
    if info is None:
        return None
    try:
        fcf = info.get('freeCashflow')
        mcap = info.get('marketCap')
        if not fcf or not mcap or mcap == 0:
            return None
        fcf, mcap = float(fcf), float(mcap)
        y = fcf / mcap
        sig = 'MENARIK' if y > 0.05 else 'NETRAL' if y > 0.02 else ('RENDAH' if y > 0 else 'NEGATIF')
        return {'fcf': fcf, 'mcap': mcap, 'yield': round(y, 4), 'signal': sig}
    except:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add indicators/risk_metrics.py && git commit -m "feat: add risk metrics with configurable risk-free rate"
```

---

### Task 10: Composite Score

**Files:**
- Create: `indicators/composite.py`

- [ ] **Step 1: Write indicators/composite.py**

```python
def calculate_composite(info, piotroski, altman, macd_bb_data, rsi_data, sharpe, sortino, rvol_data, hist_1y):
    try:
        pe = min(float(info.get('trailingPE') or 50), 100)
        pb = min(float(info.get('priceToBook') or 5), 20)
        roe = float(info.get('returnOnEquity') or 0) * 100
        cr = float(info.get('currentRatio') or 1)
        de = float(info.get('debtToEquity') or 100)

        val_sc = max(0, min(30, (50 - pe) / 50 * 30)) if pe > 0 else 0
        prof_sc = min(25, roe * 0.8) if roe > 0 else 0
        hlth_sc = max(0, min(20, cr / 3 * 20) - (de / 100 - 1) * 5 if cr > 0 else 0)
        f_base = (val_sc + prof_sc + hlth_sc) / 75 * 100
        p_bonus = (piotroski['score'] / 9 * 100) if piotroski else 50
        fund = f_base * 0.5 + p_bonus * 0.5

        tech = 50
        if macd_bb_data:
            bb_t = max(0, 100 - macd_bb_data['bb']['pct_b'] * 100)
            macd_t = 70 if macd_bb_data['macd']['signal_label'] == 'BULLISH' else 30
            tech = bb_t * 0.5 + macd_t * 0.5

        risk = 50
        if sharpe is not None:
            risk = max(0, min(80, 40 + sharpe * 15))
        if sortino is not None:
            sor = max(0, min(80, 40 + sortino * 15))
            risk = (risk + sor) / 2
        if altman:
            if altman['zone'] == 'AMAN':
                risk = min(100, risk + 15)
            elif altman['zone'] == 'BAHAYA':
                risk = max(0, risk - 30)

        mom = 50
        if hist_1y is not None and len(hist_1y) > 126:
            try:
                h = hist_1y['Close']
                m1 = (h.iloc[-1] / h.iloc[-22] - 1) * 100 if len(h) > 22 else 0
                m3 = (h.iloc[-1] / h.iloc[-66] - 1) * 100 if len(h) > 66 else 0
                m6 = (h.iloc[-1] / h.iloc[-126] - 1) * 100 if len(h) > 126 else 0
                mom = max(0, min(100, 50 + m1 * 0.3 + m3 * 0.4 + m6 * 0.3))
            except:
                pass

        sent = 50
        if rvol_data:
            sent = max(0, min(90, 50 + (rvol_data['rvol'] - 1) * 20))
        rec = (info.get('recommendationKey') or '').lower().replace('_', '')
        boosts = {'strongbuy': 20, 'buy': 10, 'hold': 0, 'neutral': 0, 'sell': -15, 'strongsell': -25}
        sent = max(0, min(100, sent + boosts.get(rec, 0)))

        final = round(min(100, max(0, fund * 0.30 + tech * 0.25 + risk * 0.20 + mom * 0.15 + sent * 0.10)), 1)
        if final >= 70:
            sig, cls = 'STRONG BUY', 'c-sb'
        elif final >= 60:
            sig, cls = 'BUY', 'c-b'
        elif final >= 45:
            sig, cls = 'HOLD', 'c-h'
        elif final >= 35:
            sig, cls = 'SELL', 'c-s'
        else:
            sig, cls = 'STRONG SELL', 'c-ss'
        return {
            'final': final,
            'signal': sig,
            'cls': cls,
            'components': {
                'Fundamental': round(fund, 1),
                'Technical': round(tech, 1),
                'Risk': round(risk, 1),
                'Momentum': round(mom, 1),
                'Sentiment': round(sent, 1),
            },
        }
    except:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add indicators/composite.py && git commit -m "feat: add composite score module (no duplicate API calls)"
```

---

### Task 11: AI Analyzer Service (GLM4.1 Air)

**Files:**
- Create: `services/ai_analyzer.py`

- [ ] **Step 1: Write services/ai_analyzer.py**

```python
import os
from openai import OpenAI


def get_client():
    return OpenAI(
        api_key=os.environ.get('GLM_API_KEY', ''),
        base_url=os.environ.get('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4'),
    )


SECTION_PROMPTS = {
    'valuasi': (
        "Analisa valuasi saham {ticker} berdasarkan data berikut: "
        "P/E {pe}, P/BV {pb}, PEG {peg}, Price to Sales {ps}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown. Langsung tulis insight saja."
    ),
    'profitabilitas': (
        "Analisa profitabilitas saham {ticker}: "
        "ROE {roe}, ROA {roa}, Net Margin {npm}, Operating Margin {opm}, "
        "Revenue Growth {rg}, Earnings Growth {eg}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'kesehatan': (
        "Analisa kesehatan keuangan saham {ticker}: "
        "Current Ratio {cr}, Quick Ratio {qr}, Debt to Equity {de}, "
        "Total Debt {td}, Total Cash {tc}, Free Cash Flow {fcf}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'dividen': (
        "Analisa dividen saham {ticker}: "
        "Dividend Yield {dy}, Dividend Rate {dr}, Payout Ratio {pr}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'technical': (
        "Analisa sinyal teknikal saham {ticker}: "
        "MACD {macd_signal}, RSI {rsi_val} ({rsi_signal}), "
        "Bollinger Bands {bb_signal} (%B {bb_pct}), Bandwidth {bb_bw}, "
        "SMA50 {sma50}, Golden Cross {gc}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'scoring': (
        "Interpretasi scoring saham {ticker}: "
        "Piotroski F-Score {fscore}/9 ({frating}), Altman Z-Score {zscore} ({zzone}). "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'composite': (
        "Beri kesimpulan akhir untuk saham {ticker} berdasarkan "
        "composite score {score}/100 dengan sinyal {signal}. "
        "Komponen: Fundamental {fund}, Technical {tech}, Risk {risk}, Momentum {mom}, Sentiment {sent}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'consensus': (
        "Rangkum consensus teknikal saham {ticker}: "
        "{buy_count} indikator bullish, {neut_count} netral, {sell_count} bearish. "
        "Verdict: {verdict}. Detail: {details}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'financial': (
        "Tren keuangan saham {ticker} berdasarkan laporan tahunan terakhir. "
        "Data: {summary}. "
        "Berikan insight singkat 2-3 kalimat tentang tren yang terlihat dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
}


def build_prompt(section, ticker, data):
    template = SECTION_PROMPTS.get(section, '')
    if not template:
        return None
    try:
        return template.format(**data)
    except KeyError:
        return template.format(ticker=ticker, **{k: v for k, v in data.items() if k in template})


def get_ai_insight(section, ticker, data):
    prompt = build_prompt(section, ticker, data)
    if not prompt:
        return None
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="glm-4-air",
            messages=[
                {"role": "system", "content": "Kamu adalah analis saham IDX yang ahli. Berikan analisis singkat, tajam, dan to the point."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.7,
            timeout=15.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Error ({section}): {e}")
        return None
```

- [ ] **Step 2: Commit**

```bash
git add services/ai_analyzer.py && git commit -m "feat: add GLM4.1 Air AI analyzer service"
```

---

### Task 12: CSS — Glassmorphism Stylesheet

**Files:**
- Create: `static/style.css`

- [ ] **Step 1: Write static/style.css**

This is the full glassmorphism CSS. Key design decisions:
- Dark mode default with `[data-theme="light"]` overrides
- Glass card: `rgba(255,255,255,0.05)` background + `backdrop-filter: blur(12px)`
- Rounded corners 12-16px
- Color: slate base, blue accent #60a5fa

```css
[data-theme="light"] {
  --bg: #f0f2f5;
  --surface: #ffffff;
  --text: #1e293b;
  --text-secondary: #64748b;
  --strong: #0f172a;
  --accent: #3b82f6;
  --pos: #10b981;
  --neg: #ef4444;
  --warn: #f59e0b;
  --info: #3b82f6;
  --glass-bg: rgba(255,255,255,0.7);
  --glass-border: rgba(0,0,0,0.06);
  --glass-shadow: 0 4px 24px rgba(0,0,0,0.06);
  --glass-blur: blur(12px);
  --border: rgba(0,0,0,0.06);
  --tab-bg: #e2e8f0;
  --tab-active: #3b82f6;
  --tab-active-text: #fff;
  --ai-bg: rgba(59,130,246,0.06);
  --ai-border: #3b82f6;
  --ai-text: #3b82f6;
  --badge-pos-bg: rgba(16,185,129,0.1);
  --badge-neg-bg: rgba(239,68,68,0.1);
  --badge-warn-bg: rgba(245,158,11,0.1);
  --badge-info-bg: rgba(59,130,246,0.1);
}

[data-theme="dark"], :root {
  --bg: #0f172a;
  --surface: rgba(255,255,255,0.05);
  --text: #e2e8f0;
  --text-secondary: #94a3b8;
  --strong: #f8fafc;
  --accent: #60a5fa;
  --pos: #34d399;
  --neg: #f87171;
  --warn: #fbbf24;
  --info: #60a5fa;
  --glass-bg: rgba(255,255,255,0.05);
  --glass-border: rgba(255,255,255,0.08);
  --glass-shadow: 0 4px 24px rgba(0,0,0,0.2);
  --glass-blur: blur(12px);
  --border: rgba(255,255,255,0.06);
  --tab-bg: rgba(255,255,255,0.06);
  --tab-active: #60a5fa;
  --tab-active-text: #fff;
  --ai-bg: rgba(96,165,250,0.06);
  --ai-border: #60a5fa;
  --ai-text: #60a5fa;
  --badge-pos-bg: rgba(52,211,153,0.12);
  --badge-neg-bg: rgba(248,113,113,0.12);
  --badge-warn-bg: rgba(251,191,36,0.12);
  --badge-info-bg: rgba(96,165,250,0.12);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Plus Jakarta Sans', sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
  transition: background 0.3s, color 0.3s;
}

.container { max-width: 960px; margin: 0 auto; padding: 0 20px 80px; }

/* HEADER */
.header {
  padding: 32px 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.header-left { display: flex; align-items: center; gap: 14px; }
.logo-mark {
  width: 40px; height: 40px;
  border-radius: 12px;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
}
.header-text h1 {
  font-size: 22px; font-weight: 800; letter-spacing: -0.5px; color: var(--strong);
}
.header-text h1 span { color: var(--accent); }
.header-text p {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; color: var(--text-secondary);
  margin-top: 2px; letter-spacing: 0.5px;
}

/* THEME TOGGLE */
.theme-toggle {
  display: flex; align-items: center; gap: 8px;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: 50px; padding: 6px 14px 6px 10px;
  cursor: pointer; user-select: none; flex-shrink: 0;
}
.toggle-track {
  width: 32px; height: 18px;
  background: var(--text-secondary);
  border-radius: 9px; position: relative; transition: background 0.3s;
}
[data-theme="light"] .toggle-track { background: var(--accent); }
.toggle-thumb {
  position: absolute; top: 2px; left: 2px;
  width: 14px; height: 14px;
  background: #fff; border-radius: 50%;
  transition: transform 0.3s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
[data-theme="light"] .toggle-thumb { transform: translateX(14px); }
.toggle-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px; color: var(--text-secondary);
  letter-spacing: 0.5px; min-width: 48px;
}

/* SEARCH */
.search-wrap {
  display: flex; margin-bottom: 28px;
  position: relative; width: 100%;
}
.search-prefix {
  position: absolute; left: 16px; top: 50%;
  transform: translateY(-50%);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px; color: var(--accent); font-weight: 600;
  z-index: 1; pointer-events: none;
}
#ticker-input {
  flex: 1;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  color: var(--text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px; font-weight: 600;
  padding: 16px 16px 16px 56px;
  outline: none; letter-spacing: 3px;
  text-transform: uppercase;
  border-radius: 14px 0 0 14px;
  transition: border-color 0.2s;
  min-width: 0;
}
#ticker-input:focus { border-color: var(--accent); }
#ticker-input::placeholder {
  color: var(--text-secondary); letter-spacing: 1px; font-size: 13px;
}
#search-btn {
  background: var(--accent); color: #fff; border: none;
  padding: 16px 28px;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 13px; font-weight: 700; letter-spacing: 0.5px;
  cursor: pointer; border-radius: 0 14px 14px 0;
  white-space: nowrap; transition: filter 0.15s;
}
#search-btn:hover { filter: brightness(1.1); }
#search-btn:disabled { background: var(--text-secondary); cursor: not-allowed; }

/* LOADING & ERROR */
#loading { display: none; text-align: center; padding: 80px 0; }
.spinner {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--glass-bg);
  border: 2px solid transparent;
  border-top-color: var(--accent);
  margin: 0 auto 16px;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
#loading p {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; color: var(--text-secondary); letter-spacing: 0.5px;
}
#error-box {
  display: none;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-left: 3px solid var(--neg);
  padding: 14px 18px; border-radius: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px; color: var(--neg);
  margin-bottom: 20px;
}
#result { display: none; }

/* GLASS CARD */
.glass {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  border-radius: 16px;
  overflow: hidden;
  animation: fadeUp 0.4s ease both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* HERO CARD */
.hero {
  padding: 24px 28px; margin-bottom: 16px;
  display: flex; justify-content: space-between;
  align-items: flex-start; gap: 20px;
}
.hero-ticker {
  font-size: 10px; color: var(--text-secondary);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 1.5px; margin-bottom: 4px;
}
.hero-name { font-size: 20px; font-weight: 700; color: var(--strong); }
.hero-tags { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.tag {
  font-size: 9px; padding: 3px 10px; border-radius: 20px;
  font-weight: 500; letter-spacing: 0.3px;
  background: var(--badge-info-bg); color: var(--accent);
}
.hero-price { text-align: right; }
.price-main {
  font-family: 'JetBrains Mono', monospace;
  font-size: 26px; font-weight: 600; color: var(--strong);
}
.price-change {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px; margin-top: 4px; font-weight: 600;
}
.up { color: var(--pos); } .down { color: var(--neg); } .neutral { color: var(--text-secondary); }

/* SECTION HEADER */
.section { margin-bottom: 16px; }
.section-header {
  display: flex; align-items: center; gap: 10px;
  padding: 16px 20px; cursor: pointer; user-select: none;
}
.section-header:hover { opacity: 0.8; }
.section-icon {
  font-size: 14px; width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: var(--glass-bg); border: 1px solid var(--glass-border);
  border-radius: 8px; flex-shrink: 0;
}
.section-title {
  font-size: 11px; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; flex: 1; color: var(--strong);
}
.section-toggle { font-size: 11px; color: var(--text-secondary); transition: transform 0.2s; }
.collapsed .section-toggle { transform: rotate(-90deg); }
.collapsed .section-body { display: none; }
.section-divider { height: 1px; background: var(--border); margin: 0 20px; }

/* KEY METRICS GRID */
.metrics-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  padding: 16px 20px;
}
.metric-card {
  background: rgba(255,255,255,0.02);
  border-radius: 12px; padding: 14px;
  border: 1px solid var(--border);
}
.metric-card-title {
  font-size: 9px; color: var(--text-secondary);
  font-weight: 600; letter-spacing: 0.5px; margin-bottom: 10px;
}
.metric-row {
  display: flex; justify-content: space-between;
  margin-bottom: 6px;
}
.metric-row:last-child { margin-bottom: 0; }
.metric-label {
  font-size: 11px; color: var(--text-secondary);
  font-weight: 500;
}
.metric-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; font-weight: 600; color: var(--strong);
}

/* COMPOSITE */
.composite-card { padding: 20px; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.composite-score-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 48px; font-weight: 600; line-height: 1;
}
.composite-info { flex: 1; min-width: 140px; }
.composite-signal {
  font-size: 12px; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; padding: 5px 14px;
  border-radius: 50px; display: inline-block;
  margin-bottom: 8px;
}
.c-sb { background: var(--badge-pos-bg); color: var(--pos); }
.c-b { background: var(--badge-pos-bg); color: var(--pos); }
.c-h { background: var(--badge-warn-bg); color: var(--warn); }
.c-s { background: var(--badge-neg-bg); color: var(--neg); }
.c-ss { background: var(--badge-neg-bg); color: var(--neg); }
.composite-bars { display: grid; gap: 8px; flex: 2; min-width: 200px; }
.cbar-row { display: flex; align-items: center; gap: 8px; }
.cbar-label {
  font-size: 11px; font-weight: 500; color: var(--text-secondary);
  width: 90px; flex-shrink: 0;
}
.cbar-track {
  flex: 1; height: 6px; background: rgba(255,255,255,0.04);
  border-radius: 3px; overflow: hidden;
}
.cbar-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--neg), var(--warn) 50%, var(--pos));
  transition: width 0.5s ease;
}
.cbar-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; color: var(--text-secondary); width: 28px; text-align: right;
}

/* DATA TABLE */
.data-table { width: 100%; border-collapse: collapse; }
.data-table td {
  padding: 9px 20px; font-size: 12px;
  border-bottom: 1px solid var(--border); vertical-align: middle;
}
.data-table tr:last-child td { border-bottom: none; }
.td-label {
  color: var(--text-secondary); font-size: 12px; font-weight: 500; width: 40%;
}
.td-val {
  font-weight: 600; font-family: 'JetBrains Mono', monospace;
  font-size: 12px; text-align: right; width: 30%;
}
.td-rating { width: 30%; padding-left: 10px; }
.badge {
  display: inline-block; font-size: 10px; padding: 3px 9px;
  border-radius: 50px; font-weight: 600;
}
.bg { background: var(--badge-pos-bg); color: var(--pos); }
.by { background: var(--badge-warn-bg); color: var(--warn); }
.bo { background: var(--badge-warn-bg); color: var(--warn); }
.br { background: var(--badge-neg-bg); color: var(--neg); }
.bb { background: var(--badge-info-bg); color: var(--info); }

/* TABS */
.tabs { display: flex; gap: 2px; padding: 0 20px; background: var(--glass-bg); }
.tab {
  font-size: 11px; font-weight: 600; padding: 10px 16px;
  cursor: pointer; border-radius: 8px 8px 0 0;
  color: var(--text-secondary); transition: all 0.2s;
  letter-spacing: 0.3px;
}
.tab:hover { color: var(--text); }
.tab.active {
  background: var(--tab-active);
  color: var(--tab-active-text);
}
.tab-content { padding: 16px 20px; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }

/* TECHNICAL CARDS */
.tech-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 16px 20px; }
.tech-card {
  background: rgba(255,255,255,0.02);
  border-radius: 12px; padding: 14px;
  border: 1px solid var(--border);
}
.tech-card-title {
  font-size: 10px; font-weight: 600; color: var(--text-secondary);
  letter-spacing: 0.5px; margin-bottom: 8px; text-transform: uppercase;
}
.tech-sig {
  font-size: 10px; font-weight: 700; padding: 3px 10px;
  border-radius: 50px; display: inline-block; margin-bottom: 8px;
}
.sig-bullish { background: var(--badge-pos-bg); color: var(--pos); }
.sig-bearish { background: var(--badge-neg-bg); color: var(--neg); }
.sig-overbought { background: var(--badge-warn-bg); color: var(--warn); }
.sig-oversold { background: var(--badge-info-bg); color: var(--info); }
.sig-netral { background: rgba(255,255,255,0.04); color: var(--text-secondary); }
.sig-golden { background: var(--badge-pos-bg); color: var(--pos); }
.sig-death { background: var(--badge-neg-bg); color: var(--neg); }
.tech-row {
  display: flex; justify-content: space-between;
  font-size: 11px; padding: 4px 0;
  border-bottom: 1px solid var(--border);
}
.tech-row:last-child { border-bottom: none; }
.tech-row-label { color: var(--text-secondary); font-weight: 500; }

/* FINANCIAL TABLE */
.table-scroll { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.fin-table { width: 100%; min-width: 560px; border-collapse: collapse; }
.fin-table th, .fin-table td {
  padding: 9px 14px; font-size: 11px;
  border-bottom: 1px solid var(--border);
  font-family: 'JetBrains Mono', monospace;
}
.fin-table th {
  color: var(--text-secondary); font-size: 10px;
  letter-spacing: 0.3px; text-transform: uppercase;
  text-align: right; font-weight: 500;
}
.fin-table th:first-child {
  text-align: left; color: var(--text);
  position: sticky; left: 0; z-index: 2;
  background: var(--glass-bg);
}
.fin-table td:first-child {
  color: var(--text-secondary); font-size: 10px;
  position: sticky; left: 0; z-index: 1;
  background: var(--glass-bg);
}
.fin-table td:not(:first-child) { text-align: right; font-weight: 600; }
.pos { color: var(--pos); } .neg { color: var(--neg); } .na { color: var(--text-secondary); opacity: 0.4; }

/* AI INSIGHT */
.ai-insight {
  margin: 0 20px 16px;
  padding: 12px 16px;
  background: var(--ai-bg);
  border-left: 3px solid var(--ai-border);
  border-radius: 0 10px 10px 0;
}
.ai-label {
  font-size: 10px; font-weight: 700; color: var(--ai-text);
  letter-spacing: 0.5px; margin-bottom: 6px;
}
.ai-text {
  font-size: 12px; color: var(--text); line-height: 1.7;
}
.ai-loading {
  font-size: 11px; color: var(--text-secondary);
  font-style: italic;
}
.ai-toggle {
  font-size: 10px; color: var(--ai-text);
  cursor: pointer; font-weight: 600;
  padding: 6px 0; display: inline-block;
}
.ai-toggle:hover { opacity: 0.8; }

/* SCORING CARDS */
.score-row {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 8px;
}
.score-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 24px; font-weight: 600; line-height: 1;
}
.score-badge {
  font-size: 10px; font-weight: 700; padding: 3px 10px;
  border-radius: 50px; letter-spacing: 0.3px;
}
.score-trend {
  font-size: 9px; padding: 2px 8px; border-radius: 20px;
  font-weight: 600;
}
.trend-up { background: var(--badge-pos-bg); color: var(--pos); }
.trend-down { background: var(--badge-neg-bg); color: var(--neg); }
.trend-stable { background: rgba(255,255,255,0.04); color: var(--text-secondary); }

/* FSCORE GRID */
.fscore-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; padding: 0 20px 16px; }
.fscore-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 0; border-bottom: 1px solid var(--border);
  font-size: 11px;
}
.fscore-item:nth-child(odd) { border-right: 1px solid var(--border); padding-right: 12px; }
.fscore-item:nth-child(even) { padding-left: 12px; }
.fscore-check {
  width: 18px; height: 18px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; flex-shrink: 0;
}
.fscore-pass { background: var(--badge-pos-bg); color: var(--pos); }
.fscore-fail { background: var(--badge-neg-bg); color: var(--neg); }
.fscore-label { font-size: 11px; font-weight: 500; color: var(--text-secondary); flex: 1; }
.fscore-val { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text); }

/* ALTMAN */
.altman-wrap { padding: 20px; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.altman-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 40px; font-weight: 600; line-height: 1;
}
.altman-zone {
  font-size: 10px; font-weight: 700; padding: 4px 12px;
  border-radius: 50px; margin-top: 8px; display: inline-block;
}
.altman-gauge { flex: 1; min-width: 180px; }
.altman-scale {
  display: flex; height: 8px; border-radius: 4px;
  overflow: hidden; margin: 8px 0 4px;
}
.altman-red { background: var(--neg); flex: 1.1; }
.altman-yellow { background: var(--warn); flex: 1.5; }
.altman-green { background: var(--pos); flex: 2.5; }
.altman-labels {
  display: flex; justify-content: space-between;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px; color: var(--text-secondary);
}

/* CONSENSUS */
.consensus-wrap { padding: 16px 20px; display: flex; gap: 16px; flex-wrap: wrap; }
.consensus-verdict { display: flex; flex-direction: column; gap: 8px; min-width: 140px; }
.consensus-badge {
  font-size: 12px; font-weight: 800; padding: 8px 14px;
  border-radius: 10px; letter-spacing: 1px;
  text-transform: uppercase; display: inline-block;
}
.consensus-counts {
  display: flex; gap: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; font-weight: 600; flex-wrap: wrap;
}
.consensus-list { flex: 1; display: flex; flex-direction: column; }
.consensus-row {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 0; border-bottom: 1px solid var(--border);
}
.consensus-row:last-child { border-bottom: none; }
.consensus-name { font-size: 11px; font-weight: 600; width: 110px; flex-shrink: 0; }
.consensus-detail {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; color: var(--text-secondary); flex: 1;
}
.consensus-vote { font-size: 12px; font-weight: 700; width: 16px; text-align: right; flex-shrink: 0; }

/* FOOTER */
.footer {
  margin-top: 40px; padding-top: 16px;
  border-top: 1px solid var(--border);
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; color: var(--text-secondary);
  letter-spacing: 0.3px; text-align: center; line-height: 2.2;
}

/* SCROLLBAR */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--text-secondary); border-radius: 3px; opacity: 0.4; }

/* RESPONSIVE */
@media (max-width: 680px) {
  .header { flex-direction: column; align-items: flex-start; gap: 16px; }
  .header-left { width: 100%; justify-content: space-between; }
  .search-wrap { flex-direction: column; gap: 10px; }
  .search-prefix { top: 16px; transform: none; }
  #ticker-input { border-radius: 12px !important; width: 100%; }
  #search-btn { border-radius: 12px !important; width: 100%; }
  .hero { flex-direction: column; padding: 20px; }
  .hero-price { text-align: left; }
  .metrics-grid { grid-template-columns: 1fr; }
  .tech-grid { grid-template-columns: 1fr; }
  .fscore-grid { grid-template-columns: 1fr; }
  .fscore-item:nth-child(odd) { border-right: none; }
  .composite-card { flex-direction: column; align-items: flex-start; }
  .tabs { overflow-x: auto; }
}
```

- [ ] **Step 2: Commit**

```bash
git add static/style.css && git commit -m "feat: add glassmorphism CSS stylesheet"
```

---

### Task 13: HTML Template

**Files:**
- Create: `templates/index.html`

- [ ] **Step 1: Write templates/index.html**

The HTML template is the shell — header, search, loading/error, result container, and footer. All dynamic content is rendered by `app.js`.

```html
<!DOCTYPE html>
<html lang="id" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IDX Analyzer</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-left">
      <div class="logo-mark">📊</div>
      <div class="header-text">
        <h1>IDX <span>ANALYZER</span></h1>
        <p>LAPORAN KEUANGAN &amp; FUNDAMENTAL — BURSA EFEK INDONESIA</p>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;color:var(--text-secondary);letter-spacing:.3px;">by <span style="color:var(--accent)">ElvanRafif</span></div>
      <div class="theme-toggle" onclick="toggleTheme()">
        <span id="t-icon" style="font-size:13px;">☀️</span>
        <div class="toggle-track"><div class="toggle-thumb"></div></div>
        <span class="toggle-label" id="t-label">Light Mode</span>
      </div>
    </div>
  </div>

  <div class="search-wrap">
    <span class="search-prefix">IDX:</span>
    <input type="text" id="ticker-input" placeholder="Ketik ticker... contoh: BBCA" maxlength="10" autocomplete="off" spellcheck="false">
    <button id="search-btn" onclick="analyze()">ANALISIS →</button>
  </div>

  <div id="error-box"></div>
  <div id="loading"><div class="spinner"></div><p>Mengambil data dari Yahoo Finance...</p></div>
  <div id="result"></div>

  <div class="footer">
    IDX ANALYZER · DATA DARI YAHOO FINANCE · DELAY ~15 MENIT<br>
    HANYA UNTUK REFERENSI — BUKAN REKOMENDASI INVESTASI
  </div>
</div>
<script src="{{ url_for('static', filename='app.js') }}"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add templates/index.html && git commit -m "feat: add glassmorphism HTML template"
```

---

### Task 14: Frontend JavaScript (app.js)

**Files:**
- Create: `static/app.js`

- [ ] **Step 1: Write static/app.js**

This is the largest file — handles theme, search, data rendering, tabs, AI insight fetching. Key functions:

- Theme toggle
- `analyze()` — fetch stock data from `/api/analyze`
- `render(d)` — render all sections
- Tab switching for Fundamental and Financial sections
- `fetchAIInsight()` — call `/api/ai-insight` per section
- AI insight typing effect

The file contains:
1. Theme management
2. Search input handling
3. Format helpers (`fnum`, `fval`, badge rendering)
4. Rating functions (same logic as current, trimmed metrics)
5. Section rendering functions (`renderHero`, `renderMetrics`, `renderComposite`, `renderConsensus`, `renderTechnical`, `renderFundamentalTabs`, `renderFinancialTabs`)
6. AI insight fetching with sessionStorage cache
7. Tab click handlers
8. `render(d)` orchestrator

Due to the size of this file (~500-600 lines), the implementer should:
- Copy rating functions (`R` object) from current `app.py` HTML (lines 369-377) — unchanged
- Copy format helpers (`fnum`, `fval`) from current HTML (lines 345-366) — unchanged
- Rewrite all `render*` functions to use new CSS classes and trimmed metrics
- Add `fetchAIInsight(ticker, section, data)` function
- Add `initTabs()` function for tab click handlers
- Replace `render_template_string` HTML rendering with DOM-based rendering

The key structural change: instead of building HTML strings for 12+ sections, build HTML for 7 consolidated sections with tab components.

- [ ] **Step 2: Commit**

```bash
git add static/app.js && git commit -m "feat: add frontend JavaScript with tabs and AI insight"
```

---

### Task 15: Flask App (Routes + Orchestrator)

**Files:**
- Create: `app.py` (rewrite)

- [ ] **Step 1: Write new app.py**

```python
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from services.yahoo_fetcher import fetch_ticker_data, df_to_dict
from services.ai_analyzer import get_ai_insight
from indicators.piotroski import calculate_piotroski
from indicators.altman_z import calculate_altman_z
from indicators.macd_bb import calculate_macd_bb
from indicators.rsi import calculate_rsi
from indicators.sma import calculate_sma
from indicators.rvol import calculate_rvol
from indicators.risk_metrics import calculate_sharpe, calculate_sortino, calculate_fcf_yield
from indicators.composite import calculate_composite

load_dotenv()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze')
def analyze():
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({"error": "Ticker tidak boleh kosong."})

    try:
        data = fetch_ticker_data(ticker)
        if data is None:
            return jsonify({"error": f"Data emiten {ticker} tidak ditemukan di IHSG."})

        info = data['info']
        bs = data['balance_sheet']
        fs = data['financials']
        cf = data['cashflow']

        sharpe = calculate_sharpe(data['hist_1y'])
        sortino = calculate_sortino(data['hist_1y'])
        piotroski = calculate_piotroski(bs, fs, cf)
        altman = calculate_altman_z(bs, fs)
        macd_bb = calculate_macd_bb(data['hist_6m'])
        rsi = calculate_rsi(data['hist_3m'])
        sma = calculate_sma(data['hist_1y'])
        rvol = calculate_rvol(data['hist_3m'])
        fcf_yield = calculate_fcf_yield(info)
        composite = calculate_composite(
            info, piotroski, altman, macd_bb, rsi,
            sharpe, sortino, rvol, data['hist_1y']
        )

        return jsonify({
            "ticker": ticker,
            "updated": data['updated'],
            "info": info,
            "financials": df_to_dict(fs),
            "balance_sheet": df_to_dict(bs),
            "cashflow": df_to_dict(cf),
            "quarterly": df_to_dict(data['quarterly']),
            "piotroski": piotroski,
            "altman": altman,
            "macd_bb": macd_bb,
            "rsi": rsi,
            "sma": sma,
            "rvol": rvol,
            "fcf_yield": fcf_yield,
            "sharpe": sharpe,
            "sortino": sortino,
            "composite": composite,
        })
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": f"Error teknis: {str(e)}"})


@app.route('/api/ai-insight', methods=['POST'])
def ai_insight():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Request body required"}), 400
    section = body.get('section', '')
    ticker = body.get('ticker', '')
    data = body.get('data', {})
    insight = get_ai_insight(section, ticker, data)
    if insight:
        return jsonify({"insight": insight})
    return jsonify({"insight": None})


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
```

- [ ] **Step 2: Commit**

```bash
git add app.py && git commit -m "feat: rewrite Flask app as slim orchestrator with modular imports"
```

---

### Task 16: Integration Test + Cleanup

**Files:**
- Delete: old `app.py` backup (already replaced)
- Verify: all imports work, server starts

- [ ] **Step 1: Test imports**

```bash
python -c "from services.yahoo_fetcher import fetch_ticker_data; print('yahoo_fetcher OK')"
python -c "from services.ai_analyzer import get_ai_insight; print('ai_analyzer OK')"
python -c "from indicators.rsi import calculate_rsi; print('rsi OK')"
python -c "from indicators.macd_bb import calculate_macd_bb; print('macd_bb OK')"
python -c "from indicators.piotroski import calculate_piotroski; print('piotroski OK')"
python -c "from indicators.composite import calculate_composite; print('composite OK')"
```

Expected: All print "OK" with no import errors.

- [ ] **Step 2: Test Flask app starts**

```bash
python app.py &
sleep 3
curl -s http://localhost:8080/ | head -20
kill %1
```

Expected: HTML returned with no errors.

- [ ] **Step 3: Test analyze endpoint**

```bash
python app.py &
sleep 3
curl -s "http://localhost:8080/api/analyze?ticker=BBCA" | python -m json.tool | head -30
kill %1
```

Expected: JSON with ticker, info, indicators populated.

- [ ] **Step 4: Test AI insight endpoint**

```bash
python app.py &
sleep 3
curl -s -X POST "http://localhost:8080/api/ai-insight" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"BBCA","section":"valuasi","data":{"pe":24.5,"pb":5.8,"peg":1.2,"ps":8.1}}' | python -m json.tool
kill %1
```

Expected: JSON with `insight` field containing AI-generated text.

- [ ] **Step 5: Final commit**

```bash
git add -A && git commit -m "feat: complete IDX Analyzer rework — modular architecture, glassmorphism UI, AI integration"
```
