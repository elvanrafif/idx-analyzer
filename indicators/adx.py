def calculate_adx(hist, period=14):
    if hist is None or len(hist) < period + 5:
        return None
    try:
        hist  = hist.dropna(subset=['Close', 'High', 'Low'])
        if len(hist) < period + 5:
            return None
        high  = hist['High']
        low   = hist['Low']
        close = hist['Close']

        prev_high  = high.shift(1)
        prev_low   = low.shift(1)
        prev_close = close.shift(1)

        tr = (high - low).combine(
            (high - prev_close).abs(), max
        ).combine(
            (low - prev_close).abs(), max
        )

        plus_dm  = high - prev_high
        minus_dm = prev_low - low

        plus_dm  = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

        atr      = tr.ewm(alpha=1/period, adjust=False).mean()
        plus_di  = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr
        minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr

        dx  = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()

        val      = round(float(adx.iloc[-1]), 1)
        plus_val = round(float(plus_di.iloc[-1]), 1)
        minus_val = round(float(minus_di.iloc[-1]), 1)

        if val >= 25:
            strength = 'STRONG'
        elif val >= 20:
            strength = 'MODERATE'
        else:
            strength = 'WEAK'

        direction = 'BULLISH' if plus_val > minus_val else 'BEARISH'

        return {
            'adx': val,
            'plus_di': plus_val,
            'minus_di': minus_val,
            'strength': strength,
            'direction': direction,
        }
    except Exception as e:
        print(f"ADX error: {e}")
        return None
