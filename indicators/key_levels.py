def _rnd(x):
    return round(x * 2) / 2  # round to nearest 0.5


def calculate_key_levels(hist):
    """Standard pivot points using last 5 trading days."""
    if hist is None or len(hist) < 5:
        return None
    try:
        hist = hist.dropna(subset=['Close', 'High', 'Low'])
        if len(hist) < 5:
            return None
        recent = hist.tail(5)
        high = float(recent['High'].max())
        low = float(recent['Low'].min())
        close = float(hist['Close'].iloc[-1])

        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)

        return {
            'current': _rnd(close),
            'pivot':   _rnd(pivot),
            'r1': _rnd(r1), 'r2': _rnd(r2), 'r3': _rnd(r3),
            's1': _rnd(s1), 's2': _rnd(s2), 's3': _rnd(s3),
        }
    except Exception as e:
        print(f"Key levels error: {e}")
        return None


def calculate_outlook(key_levels, composite, atr=None):
    """Generate trading outlook from key levels and composite score."""
    if not key_levels:
        return None
    try:
        current = key_levels['current']
        score = (composite or {}).get('final', 50)
        s1, s2 = key_levels['s1'], key_levels['s2']
        r1, r2, r3 = key_levels['r1'], key_levels['r2'], key_levels['r3']

        if current <= r1:
            entry_low, entry_high = s1, r1
            t1, t2 = r1, r2
            bull_break, bear_drop = r1, s1
            stop_loss = s2
        else:
            entry_low, entry_high = r1, current
            t1, t2 = r2, r3
            bull_break, bear_drop = r2, r1
            stop_loss = s1

        entry_mid = (entry_low + entry_high) / 2

        # ATR-based stop loss overrides pivot-based when available
        if atr and atr.get('value') and entry_mid:
            stop_loss = round(entry_mid - 2 * atr['value'], 0)
            sl_pct    = round(2 * atr['pct'], 1)
        else:
            sl_pct = abs((entry_mid - stop_loss) / entry_mid * 100) if entry_mid else 0
        t1_pct = (t1 - entry_mid) / entry_mid * 100 if entry_mid else 0
        t2_pct = (t2 - entry_mid) / entry_mid * 100 if entry_mid else 0
        rr = round(t2_pct / sl_pct, 1) if sl_pct > 0 else 0

        if score >= 65:   action, action_cls = 'ACCUMULATE', 'bull'
        elif score >= 50: action, action_cls = 'HOLD', 'neutral'
        elif score >= 35: action, action_cls = 'REDUCE', 'bear'
        else:             action, action_cls = 'AVOID', 'bear'

        def f(x):
            s = f"{x:,.1f}"
            return 'Rp ' + s.replace(',', '.')

        return {
            'bull': f"Breakout di atas {f(bull_break)} dengan target {f(t2)}",
            'bear': f"Koreksi ke support {f(bear_drop)} jika gagal break resistance",
            'action': action,
            'action_cls': action_cls,
            'entry_low': entry_low,
            'entry_high': entry_high,
            'entry_mid': round(entry_mid, 1),
            'stop_loss': stop_loss,
            'sl_pct': round(sl_pct, 1),
            'target1': t1,
            't1_pct': round(t1_pct, 1),
            'target2': t2,
            't2_pct': round(t2_pct, 1),
            'rr_ratio': rr,
        }
    except Exception as e:
        print(f"Outlook error: {e}")
        return None
