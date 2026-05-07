def calculate_obv(hist):
    if hist is None or len(hist) < 20:
        return None
    try:
        hist   = hist.dropna(subset=['Close', 'Volume'])
        if len(hist) < 20:
            return None

        close  = hist['Close']
        volume = hist['Volume']

        direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        obv_series = (direction * volume).cumsum()

        ema10 = obv_series.ewm(span=10, adjust=False).mean()

        obv_now  = float(obv_series.iloc[-1])
        obv_prev = float(obv_series.iloc[-6])
        ema_now  = float(ema10.iloc[-1])
        ema_prev = float(ema10.iloc[-6])

        price_up  = float(close.iloc[-1]) > float(close.iloc[-6])
        obv_up    = obv_now > obv_prev
        ema_up    = ema_now > ema_prev

        if obv_up and not price_up:
            signal = 'BULLISH DIVERGENCE'
        elif not obv_up and price_up:
            signal = 'BEARISH DIVERGENCE'
        elif obv_up and ema_up:
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
    except:
        return None
