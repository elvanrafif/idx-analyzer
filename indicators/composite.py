def calculate_composite(info, piotroski, altman, macd_bb_data, rsi_data,
                         sharpe, sortino, rvol_data, hist_1y,
                         adx_data=None, stoch_data=None, obv_data=None,
                         mfi_data=None, willr_data=None):
    try:
        # --- Fundamental (28%) ---
        pe  = min(float(info.get('trailingPE') or 50), 100)
        pb  = min(float(info.get('priceToBook') or 5), 20)
        roe = float(info.get('returnOnEquity') or 0) * 100
        cr  = float(info.get('currentRatio') or 1)
        de  = float(info.get('debtToEquity') or 100)

        val_sc  = max(0, min(30, (50 - pe) / 50 * 30)) if pe > 0 else 0
        prof_sc = min(25, roe * 0.8) if roe > 0 else 0
        hlth_sc = max(0, min(20, cr / 3 * 20) - (de / 100 - 1) * 5 if cr > 0 else 0)
        f_base  = (val_sc + prof_sc + hlth_sc) / 75 * 100
        p_bonus = (piotroski['score'] / 9 * 100) if piotroski else 50
        fund    = f_base * 0.5 + p_bonus * 0.5

        # EV/EBITDA bonus/penalty
        ev_ebitda = info.get('enterpriseToEbitda')
        if ev_ebitda:
            ev = float(ev_ebitda)
            if 0 < ev < 8:
                fund = min(100, fund + 5)
            elif ev > 15:
                fund = max(0, fund - 5)

        # Dividend yield bonus
        dy = info.get('dividendYield')
        if dy and float(dy) * 100 >= 4:
            fund = min(100, fund + 5)

        # --- Technical (32%) — 8 indicators ---
        scores = []

        if macd_bb_data:
            # MACD: 20% weight
            macd_score = 70 if macd_bb_data['macd']['signal_label'] == 'BULLISH' else 30
            if macd_bb_data['macd']['hist'] > 0:
                macd_score = min(100, macd_score + 10)
            else:
                macd_score = max(0, macd_score - 10)
            scores.append((macd_score, 0.20))

            # BB: 15% weight — lower pct_b = more bullish
            bb_score = (1 - macd_bb_data['bb']['pct_b']) * 100
            scores.append((bb_score, 0.15))

        if rsi_data:
            # RSI: 15% — inverse linear (RSI 30 → 70, RSI 70 → 30)
            rsi_score = 100 - rsi_data['value']
            scores.append((rsi_score, 0.15))

        if stoch_data:
            # Stochastic: 15% — inverse of K
            stoch_score = 100 - stoch_data['k']
            if stoch_data.get('cross') == 'GOLDEN CROSS':
                stoch_score = min(100, stoch_score + 10)
            elif stoch_data.get('cross') == 'DEATH CROSS':
                stoch_score = max(0, stoch_score - 10)
            scores.append((stoch_score, 0.15))

        if adx_data:
            # ADX: 15% — strong trend direction, weak = neutral
            if adx_data['strength'] == 'WEAK':
                adx_score = 50
            elif adx_data['direction'] == 'BULLISH':
                adx_score = 70 if adx_data['strength'] == 'STRONG' else 60
            else:
                adx_score = 30 if adx_data['strength'] == 'STRONG' else 40
            scores.append((adx_score, 0.15))

        if obv_data:
            # OBV: 10%
            obv_map = {
                'ACCUMULATION': 75, 'BULLISH DIVERGENCE': 80,
                'DISTRIBUTION': 25, 'BEARISH DIVERGENCE': 20,
                'NEUTRAL': 50,
            }
            obv_score = obv_map.get(obv_data['signal'], 50)
            scores.append((obv_score, 0.10))

        if mfi_data:
            # MFI: 5% — inverse linear like RSI
            mfi_score = 100 - mfi_data['value']
            scores.append((mfi_score, 0.05))

        if willr_data:
            # Williams %R: 5% — value is -100 to 0, negate for bullish score
            willr_score = -willr_data['value']  # -(-80) = 80 (oversold=bullish)
            scores.append((willr_score, 0.05))

        if scores:
            total_weight = sum(w for _, w in scores)
            tech = sum(s * w for s, w in scores) / total_weight
        else:
            tech = 50

        # --- Risk (20%) ---
        risk = 50
        if sharpe is not None:
            risk = max(0, min(80, 40 + sharpe * 15))
        if sortino is not None:
            sor  = max(0, min(80, 40 + sortino * 15))
            risk = (risk + sor) / 2
        if altman:
            if altman['zone'] == 'AMAN':
                risk = min(100, risk + 15)
            elif altman['zone'] == 'BAHAYA':
                risk = max(0, risk - 30)

        # --- Momentum (13%) ---
        mom = 50
        if hist_1y is not None and len(hist_1y) > 126:
            try:
                h  = hist_1y['Close']
                m1 = (h.iloc[-1] / h.iloc[-22]  - 1) * 100 if len(h) > 22  else 0
                m3 = (h.iloc[-1] / h.iloc[-66]  - 1) * 100 if len(h) > 66  else 0
                m6 = (h.iloc[-1] / h.iloc[-126] - 1) * 100 if len(h) > 126 else 0
                mom = max(0, min(100, 50 + m1 * 0.3 + m3 * 0.4 + m6 * 0.3))
            except:
                pass

        # --- Sentiment (7%) ---
        sent = 50
        if rvol_data:
            sent = max(0, min(90, 50 + (rvol_data['rvol'] - 1) * 20))
        rec    = (info.get('recommendationKey') or '').lower().replace('_', '')
        boosts = {'strongbuy': 20, 'buy': 10, 'hold': 0, 'neutral': 0, 'sell': -15, 'strongsell': -25}
        sent   = max(0, min(100, sent + boosts.get(rec, 0)))

        final = round(min(100, max(0,
            fund * 0.28 + tech * 0.32 + risk * 0.20 + mom * 0.13 + sent * 0.07
        )), 1)

        if final >= 70:   sig, cls = 'STRONG BUY',  'c-sb'
        elif final >= 60: sig, cls = 'BUY',          'c-b'
        elif final >= 45: sig, cls = 'HOLD',         'c-h'
        elif final >= 35: sig, cls = 'SELL',         'c-s'
        else:             sig, cls = 'STRONG SELL',  'c-ss'

        return {
            'final': final,
            'signal': sig,
            'cls': cls,
            'components': {
                'Fundamental': round(fund, 1),
                'Technical':   round(tech, 1),
                'Risk':        round(risk, 1),
                'Momentum':    round(mom, 1),
                'Sentiment':   round(sent, 1),
            },
        }
    except:
        return None
