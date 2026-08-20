from datetime import datetime, timedelta, timezone

# IDX regular session, WIB: 09:00-11:30 then 13:30-15:00 (Mon-Thu; Fri 14:50).
# ponytail: fixed schedule, no holiday/half-day calendar. Add one if the
# prorated RVOL starts lying on shortened sessions.
_WIB = timezone(timedelta(hours=7))
_SESSIONS = ((9 * 60, 11 * 60 + 30), (13 * 60 + 30, 15 * 60))
_FULL_SESSION_MIN = sum(end - start for start, end in _SESSIONS)


def session_fraction(now=None):
    """How much of today's trading session has elapsed, in (0, 1]."""
    now = now or datetime.now(_WIB)
    minutes = now.hour * 60 + now.minute
    elapsed = sum(
        max(0, min(minutes, end) - start)
        for start, end in _SESSIONS
    )
    if elapsed <= 0:
        return 1.0  # pre-open: the last bar is a completed prior day
    return min(1.0, elapsed / _FULL_SESSION_MIN)


def calculate_rvol(hist_3m, now=None):
    if hist_3m is None or len(hist_3m) < 21:
        return None
    try:
        avg = float(hist_3m['Volume'].iloc[:-1].tail(20).mean())
        today = float(hist_3m['Volume'].iloc[-1])
        if avg == 0:
            return None

        # Is the last bar today's, still filling up? If so, compare like for
        # like by projecting it to a full session instead of pitting a partial
        # day against 20 complete ones.
        now = now or datetime.now(_WIB)
        last_date = hist_3m.index[-1].date()
        frac = session_fraction(now) if last_date == now.date() else 1.0
        partial = frac < 1.0

        rvol = (today / frac) / avg
        sig = 'SANGAT TINGGI' if rvol > 3 else 'TINGGI' if rvol > 2 else 'NORMAL' if rvol > 0.7 else 'RENDAH'
        return {
            'rvol': round(rvol, 2),
            'today': int(today),
            'avg': int(avg),
            'signal': sig,
            'partial': partial,
            'session_pct': round(frac * 100),
        }
    except Exception as e:
        print(f"RVOL error: {e}")
        return None
