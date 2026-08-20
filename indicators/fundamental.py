_FINANCIAL_SECTORS = ('financial services', 'financial', 'financials')


def is_financial(info):
    """Banks/insurers: no working capital, no gross profit, no current ratio.
    Altman Z and half of Piotroski are undefined for them."""
    sector = ((info or {}).get('sector') or '').strip().lower()
    industry = ((info or {}).get('industry') or '').strip().lower()
    return sector in _FINANCIAL_SECTORS or 'bank' in industry or 'insurance' in industry


def _f(info, key):
    try:
        v = float((info or {}).get(key))
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def dividend_yield_pct(info):
    """Trailing dividend yield in percent, or None.

    Two traps here. (1) yfinance >= 0.2.52 returns info['dividendYield']
    already in percent (BBCA -> 5.65 meaning 5.65%), not as a fraction.
    (2) That field is the FORWARD/indicated yield, which annualises the last
    payout and badly overstates lumpy IDX dividends -- UNVR prints 12.81%
    forward against 6.40% actually paid over the last 12 months. So trailing
    wins, and dividendYield is only the fallback.
    """
    trailing = _f(info, 'trailingAnnualDividendYield')
    if trailing is not None:
        return trailing * 100 if trailing < 0.5 else trailing
    dy = _f(info, 'dividendYield')
    if dy is None:
        return None
    return dy * 100 if dy < 0.5 else dy


def forward_dividend_yield_pct(info):
    """Yahoo's indicated/forward yield, for display alongside the trailing one."""
    dy = _f(info, 'dividendYield')
    if dy is None:
        return None
    return dy * 100 if dy < 0.5 else dy


def calculate_dividend_yield(info):
    if info is None:
        return None
    try:
        pct = dividend_yield_pct(info)
        if pct is None:
            return {'yield': 0, 'yield_pct': 0, 'signal': 'TIDAK ADA'}
        pct = round(pct, 2)
        if pct >= 4:
            signal = 'MENARIK'
        elif pct >= 2:
            signal = 'MODERAT'
        elif pct > 0:
            signal = 'RENDAH'
        else:
            signal = 'TIDAK ADA'
        fwd = forward_dividend_yield_pct(info)
        return {
            'yield': round(pct / 100, 4),
            'yield_pct': pct,
            'forward_pct': round(fwd, 2) if fwd is not None else None,
            'signal': signal,
        }
    except Exception as e:
        print(f"Dividend yield error: {e}")
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
    except Exception as e:
        print(f"EV/EBITDA error: {e}")
        return None
