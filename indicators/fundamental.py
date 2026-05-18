def calculate_dividend_yield(info):
    if info is None:
        return None
    try:
        dy = info.get('dividendYield')
        if dy is None:
            return {'yield': 0, 'yield_pct': 0, 'signal': 'TIDAK ADA'}
        dy = float(dy)
        pct = round(dy * 100, 2)
        if pct >= 4:
            signal = 'MENARIK'
        elif pct >= 2:
            signal = 'MODERAT'
        elif pct > 0:
            signal = 'RENDAH'
        else:
            signal = 'TIDAK ADA'
        return {'yield': dy, 'yield_pct': pct, 'signal': signal}
    except:
        return None


def calculate_ev_ebitda(info):
    if info is None:
        return None
    try:
        ev_ebitda = info.get('enterpriseToEbitda')
        if ev_ebitda is None:
            return None
        val = float(ev_ebitda)
        if val <= 0:
            return None
        if val < 8:
            signal = 'MURAH'
        elif val <= 15:
            signal = 'WAJAR'
        else:
            signal = 'MAHAL'
        return {'value': round(val, 1), 'signal': signal}
    except:
        return None
