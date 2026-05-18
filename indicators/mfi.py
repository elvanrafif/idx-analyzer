import pandas as pd

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
