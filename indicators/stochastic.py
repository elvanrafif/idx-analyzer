def calculate_stochastic(hist, k_period=14, d_period=3):
    if hist is None or len(hist) < k_period + d_period + 5:
        return None
    try:
        hist  = hist.dropna(subset=['Close', 'High', 'Low'])
        if len(hist) < k_period + d_period + 5:
            return None

        high  = hist['High']
        low   = hist['Low']
        close = hist['Close']

        lowest_low   = low.rolling(k_period).min()
        highest_high = high.rolling(k_period).max()

        fast_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        slow_k = fast_k.rolling(d_period).mean()
        slow_d = slow_k.rolling(d_period).mean()

        k = round(float(slow_k.iloc[-1]), 1)
        d = round(float(slow_d.iloc[-1]), 1)
        k_prev = float(slow_k.iloc[-2])
        d_prev = float(slow_d.iloc[-2])

        if k > 80:
            signal = 'OVERBOUGHT'
        elif k < 20:
            signal = 'OVERSOLD'
        elif k > d and k_prev <= d_prev:
            signal = 'BULLISH'
        elif k < d and k_prev >= d_prev:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'

        cross = None
        if k > d and k_prev <= d_prev:
            cross = 'GOLDEN CROSS'
        elif k < d and k_prev >= d_prev:
            cross = 'DEATH CROSS'

        return {
            'k': k,
            'd': d,
            'signal': signal,
            'cross': cross,
        }
    except:
        return None
