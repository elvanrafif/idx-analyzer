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
