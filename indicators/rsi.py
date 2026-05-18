def calculate_rsi(hist_3m, period=14):
    if hist_3m is None or len(hist_3m) < period + 1:
        return None
    try:
        close = hist_3m['Close']
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta.clip(upper=0))

        # Wilder's smoothing: SMA seed for first `period` bars, then EWM
        avg_gain = gain.iloc[1:period+1].mean()
        avg_loss = loss.iloc[1:period+1].mean()
        gains = gain.iloc[period+1:]
        losses = loss.iloc[period+1:]
        for g, l in zip(gains, losses):
            avg_gain = (avg_gain * (period - 1) + g) / period
            avg_loss = (avg_loss * (period - 1) + l) / period

        rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
        val = round(100 - (100 / (1 + rs)), 1)
        signal = 'OVERBOUGHT' if val > 70 else 'OVERSOLD' if val < 30 else 'NEUTRAL'
        return {'value': val, 'signal': signal}
    except:
        return None
