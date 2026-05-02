def calculate_sma(hist_1y):
    if hist_1y is None or len(hist_1y) < 50:
        return None
    try:
        close = hist_1y['Close']
        price = round(float(close.iloc[-1]), 0)
        ema20 = round(float(close.ewm(span=20, adjust=False).mean().iloc[-1]), 0)
        sma50 = round(float(close.rolling(50).mean().iloc[-1]), 0)
        sma200 = round(float(close.rolling(200).mean().iloc[-1]), 0) if len(close) >= 200 else None
        golden_cross = bool(sma50 > sma200) if sma200 else None
        return {
            'price': price,
            'ema20': ema20,
            'sma50': sma50,
            'sma200': sma200,
            'above_sma50': price > sma50,
            'golden_cross': golden_cross,
        }
    except:
        return None
