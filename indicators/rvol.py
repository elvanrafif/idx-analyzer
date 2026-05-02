def calculate_rvol(hist_3m):
    if hist_3m is None or len(hist_3m) < 21:
        return None
    try:
        avg = float(hist_3m['Volume'].iloc[:-1].tail(20).mean())
        today = float(hist_3m['Volume'].iloc[-1])
        if avg == 0:
            return None
        rvol = today / avg
        sig = 'SANGAT TINGGI' if rvol > 3 else 'TINGGI' if rvol > 2 else 'NORMAL' if rvol > 0.7 else 'RENDAH'
        return {'rvol': round(rvol, 2), 'today': int(today), 'avg': int(avg), 'signal': sig}
    except:
        return None
