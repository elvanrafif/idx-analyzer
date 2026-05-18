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
