import pandas as pd


def _get_value(df, col_idx, *keys):
    if df is None or col_idx >= len(df.columns):
        return None
    col = df.columns[col_idx]
    for key in keys:
        for idx in df.index:
            if key.lower() in str(idx).lower():
                try:
                    v = df.loc[idx, col]
                    return None if pd.isna(v) else float(v)
                except:
                    pass
    return None


def calculate_piotroski(balance_sheet, financials, cashflow):
    if balance_sheet is None or balance_sheet.empty:
        return None
    if financials is None or financials.empty:
        return None
    if cashflow is None or cashflow.empty:
        return None
    if len(balance_sheet.columns) < 2 or len(financials.columns) < 2:
        return None

    try:
        bs, fs, cf = balance_sheet, financials, cashflow

        ta0 = _get_value(bs, 0, 'total assets')
        ta1 = _get_value(bs, 1, 'total assets')
        ni0 = _get_value(fs, 0, 'net income')
        ni1 = _get_value(fs, 1, 'net income')
        ocf0 = _get_value(cf, 0, 'operating cash flow')
        ltd0 = _get_value(bs, 0, 'long term debt')
        ltd1 = _get_value(bs, 1, 'long term debt')
        ca0 = _get_value(bs, 0, 'current assets')
        cl0 = _get_value(bs, 0, 'current liabilities')
        ca1 = _get_value(bs, 1, 'current assets')
        cl1 = _get_value(bs, 1, 'current liabilities')
        sh0 = _get_value(bs, 0, 'ordinary shares', 'common stock')
        sh1 = _get_value(bs, 1, 'ordinary shares', 'common stock')
        gp0 = _get_value(fs, 0, 'gross profit')
        rev0 = _get_value(fs, 0, 'total revenue')
        gp1 = _get_value(fs, 1, 'gross profit')
        rev1 = _get_value(fs, 1, 'total revenue')

        avg_ta0 = (ta0 + ta1) / 2 if ta0 and ta1 else ta0
        avg_ta1 = None
        ta2 = _get_value(bs, 2, 'total assets')
        if ta1 and ta2:
            avg_ta1 = (ta1 + ta2) / 2
        elif ta1:
            avg_ta1 = ta1

        score = 0
        details = {}

        roa0 = ni0 / avg_ta0 if ni0 and avg_ta0 else None
        roa1 = ni1 / avg_ta1 if ni1 and avg_ta1 else None

        f1 = 1 if roa0 and roa0 > 0 else 0
        score += f1
        details['F1'] = {'label': 'ROA Positif', 'pass': bool(f1),
                         'value': f'{roa0*100:.1f}%' if roa0 else '—'}

        f2 = 1 if ocf0 and ocf0 > 0 else 0
        score += f2
        details['F2'] = {'label': 'Arus Kas Operasi > 0', 'pass': bool(f2),
                         'value': f'Rp {ocf0/1e9:.1f}M' if ocf0 else '—'}

        f3 = 1 if roa0 and roa1 and roa0 > roa1 else 0
        score += f3
        details['F3'] = {'label': 'ROA Meningkat YoY', 'pass': bool(f3),
                         'value': f'{roa0*100:.1f}% vs {roa1*100:.1f}%' if (roa0 and roa1) else '—'}

        ocf_ta = ocf0 / ta0 if ocf0 and ta0 else None
        f4 = 1 if ocf_ta and roa0 and ocf_ta > roa0 else 0
        score += f4
        details['F4'] = {'label': 'Kualitas Laba (OCF>NI)', 'pass': bool(f4),
                         'value': f'{ocf_ta*100:.1f}% vs {roa0*100:.1f}%' if (ocf_ta and roa0) else '—'}

        lev0 = ltd0 / ta0 if ltd0 is not None and ta0 else None
        lev1 = ltd1 / ta1 if ltd1 is not None and ta1 else None
        f5 = 1 if lev0 is not None and lev1 is not None and lev0 <= lev1 else 0
        score += f5
        details['F5'] = {'label': 'Leverage Tidak Naik', 'pass': bool(f5),
                         'value': f'{lev0*100:.1f}% vs {lev1*100:.1f}%' if (lev0 is not None and lev1 is not None) else '—'}

        cr0 = ca0 / cl0 if ca0 and cl0 else None
        cr1 = ca1 / cl1 if ca1 and cl1 else None
        f6 = 1 if cr0 and cr1 and cr0 >= cr1 else 0
        score += f6
        details['F6'] = {'label': 'Current Ratio Tidak Turun', 'pass': bool(f6),
                         'value': f'{cr0:.2f} vs {cr1:.2f}' if (cr0 and cr1) else '—'}

        f7 = 1 if sh0 and sh1 and sh0 <= sh1 * 1.02 else 0
        score += f7
        details['F7'] = {'label': 'Tidak Ada Dilusi Saham', 'pass': bool(f7),
                         'value': f'{sh0/1e9:.2f}B vs {sh1/1e9:.2f}B' if (sh0 and sh1) else '—'}

        gm0 = gp0 / rev0 if gp0 and rev0 else None
        gm1 = gp1 / rev1 if gp1 and rev1 else None
        f8 = 1 if gm0 and gm1 and gm0 >= gm1 else 0
        score += f8
        details['F8'] = {'label': 'Gross Margin Tidak Turun', 'pass': bool(f8),
                         'value': f'{gm0*100:.1f}% vs {gm1*100:.1f}%' if (gm0 and gm1) else '—'}

        at0 = rev0 / ta0 if rev0 and ta0 else None
        at1 = rev1 / ta1 if rev1 and ta1 else None
        f9 = 1 if at0 and at1 and at0 >= at1 else 0
        score += f9
        details['F9'] = {'label': 'Asset Turnover Tidak Turun', 'pass': bool(f9),
                         'value': f'{at0:.2f}x vs {at1:.2f}x' if (at0 and at1) else '—'}

        prev_score = None
        if len(bs.columns) >= 3 and len(fs.columns) >= 3:
            try:
                prev_score = _quick_piotroski(bs, fs, cf)
            except:
                pass

        trend = None
        if prev_score is not None:
            trend = 'NAIK' if score > prev_score else 'TURUN' if score < prev_score else 'STABIL'

        rating = 'KUAT' if score >= 7 else 'CUKUP' if score >= 5 else 'LEMAH'
        return {
            'score': score,
            'max': 9,
            'rating': rating,
            'trend': trend,
            'details': details,
        }
    except:
        return None


def _quick_piotroski(bs, fs, cf):
    ta0 = _get_value(bs, 1, 'total assets')
    ta1 = _get_value(bs, 2, 'total assets')
    ni0 = _get_value(fs, 1, 'net income')
    ocf0 = _get_value(cf, 1, 'operating cash flow') if len(cf.columns) >= 2 else None
    if not ta0 or not ni0:
        return None
    avg_ta = (ta0 + ta1) / 2 if ta0 and ta1 else ta0
    s = 0
    roa = ni0 / avg_ta if avg_ta else None
    if roa and roa > 0: s += 1
    if ocf0 and ocf0 > 0: s += 1
    if roa: s += 1
    ocf_ta = ocf0 / ta0 if ocf0 and ta0 else None
    if ocf_ta and roa and ocf_ta > roa: s += 1
    ltd0 = _get_value(bs, 1, 'long term debt')
    ltd1 = _get_value(bs, 2, 'long term debt')
    lev0 = ltd0 / ta0 if ltd0 is not None and ta0 else None
    lev1 = ltd1 / ta1 if ltd1 is not None and ta1 else None
    if lev0 is not None and lev1 is not None and lev0 <= lev1: s += 1
    ca0 = _get_value(bs, 1, 'current assets')
    cl0 = _get_value(bs, 1, 'current liabilities')
    ca1 = _get_value(bs, 2, 'current assets')
    cl1 = _get_value(bs, 2, 'current liabilities')
    cr0 = ca0 / cl0 if ca0 and cl0 else None
    cr1 = ca1 / cl1 if ca1 and cl1 else None
    if cr0 and cr1 and cr0 >= cr1: s += 1
    sh0 = _get_value(bs, 1, 'ordinary shares', 'common stock')
    sh1 = _get_value(bs, 2, 'ordinary shares', 'common stock')
    if sh0 and sh1 and sh0 <= sh1 * 1.02: s += 1
    gp0 = _get_value(fs, 1, 'gross profit')
    rev0 = _get_value(fs, 1, 'total revenue')
    gp1 = _get_value(fs, 2, 'gross profit')
    rev1 = _get_value(fs, 2, 'total revenue')
    gm0 = gp0 / rev0 if gp0 and rev0 else None
    gm1 = gp1 / rev1 if gp1 and rev1 else None
    if gm0 and gm1 and gm0 >= gm1: s += 1
    at0 = rev0 / ta0 if rev0 and ta0 else None
    at1 = rev1 / ta1 if rev1 and ta1 else None
    if at0 and at1 and at0 >= at1: s += 1
    return s
