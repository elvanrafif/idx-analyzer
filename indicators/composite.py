def calculate_composite(info, piotroski, altman, macd_bb_data, rsi_data, sharpe, sortino, rvol_data, hist_1y):
    try:
        pe = min(float(info.get('trailingPE') or 50), 100)
        pb = min(float(info.get('priceToBook') or 5), 20)
        roe = float(info.get('returnOnEquity') or 0) * 100
        cr = float(info.get('currentRatio') or 1)
        de = float(info.get('debtToEquity') or 100)

        val_sc = max(0, min(30, (50 - pe) / 50 * 30)) if pe > 0 else 0
        prof_sc = min(25, roe * 0.8) if roe > 0 else 0
        hlth_sc = max(0, min(20, cr / 3 * 20) - (de / 100 - 1) * 5 if cr > 0 else 0)
        f_base = (val_sc + prof_sc + hlth_sc) / 75 * 100
        p_bonus = (piotroski['score'] / 9 * 100) if piotroski else 50
        fund = f_base * 0.5 + p_bonus * 0.5

        tech = 50
        if macd_bb_data:
            bb_t = max(0, 100 - macd_bb_data['bb']['pct_b'] * 100)
            macd_t = 70 if macd_bb_data['macd']['signal_label'] == 'BULLISH' else 30
            tech = bb_t * 0.5 + macd_t * 0.5

        risk = 50
        if sharpe is not None:
            risk = max(0, min(80, 40 + sharpe * 15))
        if sortino is not None:
            sor = max(0, min(80, 40 + sortino * 15))
            risk = (risk + sor) / 2
        if altman:
            if altman['zone'] == 'AMAN':
                risk = min(100, risk + 15)
            elif altman['zone'] == 'BAHAYA':
                risk = max(0, risk - 30)

        mom = 50
        if hist_1y is not None and len(hist_1y) > 126:
            try:
                h = hist_1y['Close']
                m1 = (h.iloc[-1] / h.iloc[-22] - 1) * 100 if len(h) > 22 else 0
                m3 = (h.iloc[-1] / h.iloc[-66] - 1) * 100 if len(h) > 66 else 0
                m6 = (h.iloc[-1] / h.iloc[-126] - 1) * 100 if len(h) > 126 else 0
                mom = max(0, min(100, 50 + m1 * 0.3 + m3 * 0.4 + m6 * 0.3))
            except:
                pass

        sent = 50
        if rvol_data:
            sent = max(0, min(90, 50 + (rvol_data['rvol'] - 1) * 20))
        rec = (info.get('recommendationKey') or '').lower().replace('_', '')
        boosts = {'strongbuy': 20, 'buy': 10, 'hold': 0, 'neutral': 0, 'sell': -15, 'strongsell': -25}
        sent = max(0, min(100, sent + boosts.get(rec, 0)))

        final = round(min(100, max(0, fund * 0.30 + tech * 0.25 + risk * 0.20 + mom * 0.15 + sent * 0.10)), 1)
        if final >= 70:
            sig, cls = 'STRONG BUY', 'c-sb'
        elif final >= 60:
            sig, cls = 'BUY', 'c-b'
        elif final >= 45:
            sig, cls = 'HOLD', 'c-h'
        elif final >= 35:
            sig, cls = 'SELL', 'c-s'
        else:
            sig, cls = 'STRONG SELL', 'c-ss'
        return {
            'final': final,
            'signal': sig,
            'cls': cls,
            'components': {
                'Fundamental': round(fund, 1),
                'Technical': round(tech, 1),
                'Risk': round(risk, 1),
                'Momentum': round(mom, 1),
                'Sentiment': round(sent, 1),
            },
        }
    except:
        return None
