import numpy as np
import os


def get_risk_free_rate():
    try:
        return float(os.environ.get('RISK_FREE_RATE', '0.065'))
    except:
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
    except:
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
        down = ret[ret < 0]
        down_std = down.std() * np.sqrt(252) if len(down) > 0 else 0
        rf = get_risk_free_rate()
        return round((ann_ret - rf) / down_std, 3) if down_std else None
    except:
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
    except:
        return None
