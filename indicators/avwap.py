def calculate_avwap(hist):
    """AVWAP anchored to start of the provided history period."""
    if hist is None or len(hist) < 5:
        return None
    try:
        close  = hist['Close']
        high   = hist['High']
        low    = hist['Low']
        volume = hist['Volume']

        typical = (high + low + close) / 3
        cum_tp_vol = (typical * volume).cumsum()
        cum_vol    = volume.cumsum()
        avwap_series = cum_tp_vol / cum_vol

        val   = round(float(avwap_series.iloc[-1]), 0)
        price = round(float(close.iloc[-1]), 0)

        signal = 'BULLISH' if price > val else 'BEARISH'
        pct_diff = round((price - val) / val * 100, 2) if val != 0 else 0

        return {
            'value': val,
            'price': price,
            'signal': signal,
            'pct_diff': pct_diff,
        }
    except:
        return None
