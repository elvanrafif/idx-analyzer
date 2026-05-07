def calculate_macd_bb(hist_6m):
    if hist_6m is None or len(hist_6m) < 30:
        return None
    try:
        hist_6m = hist_6m.dropna(subset=['Close'])
        if len(hist_6m) < 30:
            return None
        close = hist_6m['Close']
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        sig = macd.ewm(span=9, adjust=False).mean()
        hst = macd - sig
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        upper = sma20 + 2 * std20
        lower = sma20 - 2 * std20
        cp = float(close.iloc[-1])
        cm = float(macd.iloc[-1])
        cs = float(sig.iloc[-1])
        ch = float(hst.iloc[-1])
        ph = float(hst.iloc[-2])
        cu = float(upper.iloc[-1])
        cl = float(lower.iloc[-1])
        csma = float(sma20.iloc[-1])
        bb_pct = (cp - cl) / (cu - cl) if (cu - cl) != 0 else 0.5
        bandwidth = round((cu - cl) / csma, 4) if csma != 0 else 0
        squeeze = bandwidth < 0.03
        msig = 'BULLISH' if cm > cs else 'BEARISH'
        threshold = cp * 0.001
        cross = None
        if ch > 0 and ph <= 0 and abs(ch) > threshold:
            cross = 'GOLDEN CROSS'
        elif ch < 0 and ph >= 0 and abs(ch) > threshold:
            cross = 'DEATH CROSS'
        bsig = 'OVERBOUGHT' if cp > cu else 'OVERSOLD' if cp < cl else ('BULLISH' if cp > csma else 'BEARISH')
        return {
            'macd': {
                'line': round(cm, 2),
                'signal': round(cs, 2),
                'hist': round(ch, 2),
                'signal_label': msig,
                'cross': cross,
            },
            'bb': {
                'upper': round(cu, 0),
                'mid': round(csma, 0),
                'lower': round(cl, 0),
                'pct_b': round(bb_pct, 2),
                'bandwidth': bandwidth,
                'squeeze': squeeze,
                'signal': bsig,
            },
        }
    except:
        return None
