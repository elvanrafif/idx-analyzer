from .fundamental import is_financial
from .piotroski import get_line_item


def calculate_altman_z(balance_sheet, financials, info=None):
    if is_financial(info):
        return None  # Z-score is not defined for banks/insurers
    if balance_sheet is None or balance_sheet.empty:
        return None
    if financials is None or financials.empty:
        return None
    try:
        bs, fs = balance_sheet, financials
        ta = get_line_item(bs, 0, 'total assets')
        ca = get_line_item(bs, 0, 'current assets')
        cl = get_line_item(bs, 0, 'current liabilities')
        re = get_line_item(bs, 0, 'retained earnings')
        te = get_line_item(bs, 0, 'stockholders equity', 'total equity')
        tl = get_line_item(bs, 0, 'total liabilities')
        ebit = get_line_item(fs, 0, 'operating income', 'ebit')
        if None in (ta, ca, cl, te, tl) or not ta or not tl:
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
    except Exception as e:
        print(f"Altman Z error: {e}")
        return None
