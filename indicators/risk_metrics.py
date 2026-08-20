import numpy as np
import os


def get_risk_free_rate():
    try:
        return float(os.environ.get('RISK_FREE_RATE', '0.065'))
    except (TypeError, ValueError):
        return 0.065


def calculate_sharpe(hist_1y):
    if hist_1y is None or len(hist_1y) < 20:
        return None
    try:
        close = hist_1y['Close']
        ret = close.pct_change().dropna()
        if len(ret) == 0:
            return None
        ann_ret = ret.mean() * 252
        ann_std = ret.std() * np.sqrt(252)
        rf = get_risk_free_rate()
        return round((ann_ret - rf) / ann_std, 3) if ann_std else None
    except Exception as e:
        print(f"Sharpe error: {e}")
        return None


def calculate_sortino(hist_1y):
    if hist_1y is None or len(hist_1y) < 20:
        return None
    try:
        close = hist_1y['Close']
        ret = close.pct_change().dropna()
        if len(ret) == 0:
            return None
        ann_ret = ret.mean() * 252
        rf = get_risk_free_rate()
        # Downside deviation = RMS of returns below the daily MAR, divided by
        # the FULL sample size (not just the losing days). ret[ret<0].std()
        # under-states it by both dropping winners from n and de-meaning.
        mar_daily = rf / 252
        shortfall = np.minimum(ret - mar_daily, 0)
        down_std = float(np.sqrt((shortfall ** 2).mean()) * np.sqrt(252))
        return round((ann_ret - rf) / down_std, 3) if down_std else None
    except Exception as e:
        print(f"Sortino error: {e}")
        return None


def calculate_fcf_yield(info):
    if info is None:
        return None
    try:
        fcf = info.get('freeCashflow')
        mcap = info.get('marketCap')
        if not fcf or not mcap or mcap == 0:
            return None
        fcf, mcap = float(fcf), float(mcap)
        y = fcf / mcap
        sig = 'MENARIK' if y > 0.05 else 'NETRAL' if y > 0.02 else ('RENDAH' if y > 0 else 'NEGATIF')
        return {'fcf': fcf, 'mcap': mcap, 'yield': round(y, 4), 'signal': sig}
    except Exception as e:
        print(f"FCF yield error: {e}")
        return None
