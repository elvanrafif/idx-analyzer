import pandas as pd


def _bsv(bs, *keys):
    col = bs.columns[0]
    for key in keys:
        for idx in bs.index:
            if key.lower() in str(idx).lower():
                try:
                    v = bs.loc[idx, col]
                    return None if pd.isna(v) else float(v)
                except:
                    pass
    return None


def _fsv(fs, *keys):
    col = fs.columns[0]
    for key in keys:
        for idx in fs.index:
            if key.lower() in str(idx).lower():
                try:
                    v = fs.loc[idx, col]
                    return None if pd.isna(v) else float(v)
                except:
                    pass
    return None


def calculate_altman_z(balance_sheet, financials):
    if balance_sheet is None or balance_sheet.empty:
        return None
    if financials is None or financials.empty:
        return None
    try:
        bs, fs = balance_sheet, financials
        ta = _bsv(bs, 'total assets')
        ca = _bsv(bs, 'current assets')
        cl = _bsv(bs, 'current liabilities')
        re = _bsv(bs, 'retained earnings')
        te = _bsv(bs, 'stockholders equity', 'total equity')
        tl = _bsv(bs, 'total liabilities')
        ebit = _fsv(fs, 'operating income', 'ebit')
        if not all([ta, ca, cl, te, tl]) or ta == 0 or tl == 0:
            return None
        X1 = (ca - cl) / ta
        X2 = (re or 0) / ta
        X3 = (ebit or 0) / ta
        X4 = te / tl
        z = 6.56 * X1 + 3.26 * X2 + 6.72 * X3 + 1.05 * X4
        zone = 'AMAN' if z > 2.6 else 'WASPADA' if z > 1.1 else 'BAHAYA'
        descs = {
            'AMAN': 'Risiko kebangkrutan rendah',
            'WASPADA': 'Grey zone — perlu monitoring',
            'BAHAYA': 'Risiko kebangkrutan tinggi',
        }
        return {
            'z_score': round(z, 2),
            'zone': zone,
            'desc': descs[zone],
            'components': {
                'X1 (Working Capital/TA)': round(X1, 3),
                'X2 (Retained Earn/TA)': round(X2, 3),
                'X3 (EBIT/TA)': round(X3, 3),
                'X4 (Equity/Liab)': round(X4, 3),
            },
        }
    except:
        return None
