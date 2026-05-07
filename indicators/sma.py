def calculate_sma(hist_1y):
    if hist_1y is None or len(hist_1y) < 50:
        return None
    try:
        close = hist_1y['Close']
        price  = round(float(close.iloc[-1]), 0)
        ema9   = round(float(close.ewm(span=9,   adjust=False).mean().iloc[-1]), 0)
        ema21  = round(float(close.ewm(span=21,  adjust=False).mean().iloc[-1]), 0)
        ema50  = round(float(close.ewm(span=50,  adjust=False).mean().iloc[-1]), 0)
        ema200 = round(float(close.ewm(span=200, adjust=False).mean().iloc[-1]), 0) if len(close) >= 100 else None
        golden_cross = bool(ema50 > ema200) if ema200 else None
        return {
            'price': price,
            'ema9': ema9,
            'ema21': ema21,
            'ema50': ema50,
            'ema200': ema200,
            'above_ema50': price > ema50,
            'above_ema200': bool(price > ema200) if ema200 else None,
            'golden_cross': golden_cross,
        }
    except:
        return None
