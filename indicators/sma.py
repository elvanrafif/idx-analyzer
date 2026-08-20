def calculate_sma(hist_1y):
    if hist_1y is None or len(hist_1y) < 50:
        return None
    try:
        close = hist_1y['Close'].dropna()
        if len(close) < 50:
            return None
        price  = round(float(close.iloc[-1]), 0)
        ema9   = round(float(close.ewm(span=9,   adjust=False).mean().iloc[-1]), 0)
        ema21  = round(float(close.ewm(span=21,  adjust=False).mean().iloc[-1]), 0)
        ema50  = round(float(close.ewm(span=50,  adjust=False).mean().iloc[-1]), 0)

        # An EMA200 seeded 100 bars ago is still mostly its own seed price.
        # Require a full span before publishing it.
        ema200_series = close.ewm(span=200, adjust=False).mean() if len(close) >= 200 else None
        ema200 = round(float(ema200_series.iloc[-1]), 0) if ema200_series is not None else None

        # 'golden_cross' means the cross happened recently, not merely that
        # EMA50 sits above EMA200 (which can be true for years).
        golden_cross = None
        cross_event = None
        if ema200_series is not None and len(close) >= 205:
            ema50_series = close.ewm(span=50, adjust=False).mean()
            above = ema50_series > ema200_series
            golden_cross = bool(above.iloc[-1])
            recent = above.iloc[-6:]
            if recent.iloc[-1] and not recent.iloc[0]:
                cross_event = 'GOLDEN CROSS'
            elif not recent.iloc[-1] and recent.iloc[0]:
                cross_event = 'DEATH CROSS'

        return {
            'price': price,
            'ema9': ema9,
            'ema21': ema21,
            'ema50': ema50,
            'ema200': ema200,
            'above_ema50': price > ema50,
            'above_ema200': bool(price > ema200) if ema200 else None,
            'golden_cross': golden_cross,
            'cross_event': cross_event,
        }
    except Exception as e:
        print(f"SMA error: {e}")
        return None
