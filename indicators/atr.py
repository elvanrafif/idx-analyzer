import pandas as pd


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
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1).dropna()

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
