import numpy as np


def _swing_points(series, left=5, right=5):
    """Indices of local highs and lows confirmed by `right` bars on each side."""
    vals = series.to_numpy(dtype=float)
    highs, lows = [], []
    for i in range(left, len(vals) - right):
        window = vals[i - left:i + right + 1]
        if vals[i] == window.max() and (window.max() > window.min()):
            highs.append(i)
        elif vals[i] == window.min() and (window.max() > window.min()):
            lows.append(i)
    return highs, lows


def _divergence(close, obv, lookback=120):
    """Compare the last two confirmed price swings against OBV at the same
    bars. A 5-bar delta is noise; a swing-to-swing comparison is the actual
    definition of divergence."""
    close = close.iloc[-lookback:]
    obv = obv.iloc[-lookback:]
    highs, lows = _swing_points(close)

    if len(highs) >= 2:
        a, b = highs[-2], highs[-1]
        if close.iloc[b] > close.iloc[a] and obv.iloc[b] < obv.iloc[a]:
            return 'BEARISH DIVERGENCE'
    if len(lows) >= 2:
        a, b = lows[-2], lows[-1]
        if close.iloc[b] < close.iloc[a] and obv.iloc[b] > obv.iloc[a]:
            return 'BULLISH DIVERGENCE'
    return None


def calculate_obv(hist):
    if hist is None or len(hist) < 60:
        return None
    try:
        hist   = hist.dropna(subset=['Close', 'Volume'])
        if len(hist) < 60:
            return None

        close  = hist['Close']
        volume = hist['Volume']

        direction = np.sign(close.diff().fillna(0))
        obv_series = (direction * volume).cumsum()

        ema10 = obv_series.ewm(span=10, adjust=False).mean()

        obv_now  = float(obv_series.iloc[-1])
        obv_prev = float(obv_series.iloc[-6])
        ema_now  = float(ema10.iloc[-1])
        ema_prev = float(ema10.iloc[-6])

        obv_up = obv_now > obv_prev
        ema_up = ema_now > ema_prev

        signal = _divergence(close, obv_series)
        if signal is None:
            if obv_up and ema_up:
                signal = 'ACCUMULATION'
            elif not obv_up and not ema_up:
                signal = 'DISTRIBUTION'
            else:
                signal = 'NEUTRAL'

        def fmt_obv(v):
            abs_v = abs(v)
            if abs_v >= 1e9:
                return f"{v/1e9:.2f}B"
            if abs_v >= 1e6:
                return f"{v/1e6:.2f}M"
            return f"{v:,.0f}"

        return {
            'value': fmt_obv(obv_now),
            'trend': 'NAIK' if obv_up else 'TURUN',
            'ema_trend': 'NAIK' if ema_up else 'TURUN',
            'signal': signal,
            'divergence': signal.endswith('DIVERGENCE'),
        }
    except Exception as e:
        print(f"OBV error: {e}")
        return None
