def idx_tick(price):
    """IDX tick size by price band (Peraturan Bursa II-A)."""
    if price < 200:
        return 1
    if price < 500:
        return 2
    if price < 2000:
        return 5
    if price < 5000:
        return 10
    return 25


def _rnd(x, tick=None):
    """Snap to a tradeable IDX price. A level at 1237.5 cannot be ordered."""
    t = tick or idx_tick(x)
    return round(round(x / t) * t, 2)


def calculate_key_levels(hist):
    """Classic pivot points from the last COMPLETED 5-day window.

    The current bar is excluded on purpose: including today's high/low makes
    every level drift during the session, so a 'resistance' printed at 10:00
    is a different number at 14:00.
    """
    if hist is None or len(hist) < 6:
        return None
    try:
        hist = hist.dropna(subset=['Close', 'High', 'Low'])
        if len(hist) < 6:
            return None
        prior = hist.iloc[-6:-1]           # last 5 completed bars
        high = float(prior['High'].max())
        low = float(prior['Low'].min())
        close = float(prior['Close'].iloc[-1])
        current = float(hist['Close'].iloc[-1])

        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)

        tick = idx_tick(current)
        return {
            'current': _rnd(current, tick),
            'pivot':   _rnd(pivot, tick),
            'r1': _rnd(r1, tick), 'r2': _rnd(r2, tick), 'r3': _rnd(r3, tick),
            's1': _rnd(s1, tick), 's2': _rnd(s2, tick), 's3': _rnd(s3, tick),
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
        tick = idx_tick(current)

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
        if not entry_mid:
            return None
        entry_mid = _rnd(entry_mid, tick)

        if atr and atr.get('value'):
            stop_loss = entry_mid - 2 * atr['value']
        # A stop must sit below the WHOLE entry range, not just below its
        # midpoint. With a wide range and a small ATR the 2xATR stop landed
        # inside the range, so anyone filling near the bottom would have their
        # stop above their own entry price.
        stop_loss = _rnd(min(stop_loss, entry_low - tick), tick)
        # Always measure the stop from the entry, never from spot: mixing the
        # two made rr compare percentages with different denominators.
        sl_pct = abs((entry_mid - stop_loss) / entry_mid * 100)

        t1_pct = (t1 - entry_mid) / entry_mid * 100
        t2_pct = (t2 - entry_mid) / entry_mid * 100
        # R:R against the FIRST target — the one actually likely to be hit.
        rr = round(t1_pct / sl_pct, 1) if sl_pct > 0 else 0

        if score >= 65:   action, action_cls = 'ACCUMULATE', 'bull'
        elif score >= 50: action, action_cls = 'HOLD', 'neutral'
        elif score >= 35: action, action_cls = 'REDUCE', 'bear'
        else:             action, action_cls = 'AVOID', 'bear'

        def f(x):
            s = f"{x:,.0f}"
            return 'Rp ' + s.replace(',', '.')

        return {
            'bull': f"Breakout di atas {f(bull_break)} dengan target {f(t2)}",
            'bear': f"Koreksi ke support {f(bear_drop)} jika gagal break resistance",
            'action': action,
            'action_cls': action_cls,
            'entry_low': entry_low,
            'entry_high': entry_high,
            'entry_mid': entry_mid,
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
