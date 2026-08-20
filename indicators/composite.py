import numpy as np

from .fundamental import dividend_yield_pct


def _num(info, key):
    """A metric Yahoo actually reported, or None. Never a made-up default —
    a bank with no currentRatio must not score as if it had one."""
    v = info.get(key)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if (np.isnan(v) or np.isinf(v)) else v


def _blend(parts):
    """parts: list of (score, weight); Nones dropped and weights renormalised."""
    parts = [(s, w) for s, w in parts if s is not None]
    if not parts:
        return None
    return sum(s * w for s, w in parts) / sum(w for _, w in parts)


DEFAULT_WEIGHTS = {
    'fundamental': 0.28, 'technical': 0.32, 'risk': 0.20,
    'momentum': 0.13, 'sentiment': 0.07,
}

# Two ways to read the same oscillator, because two strategies disagree about
# what a high reading means.
#
#   mean_reversion — the investor's reading. Deep oversold is an opportunity,
#     the 50-70 band is a trend worth riding, above 80 is extended and risky.
#     Peaks at RSI 65 and falls off hard after 80.
#
#   momentum — the breakout trader's reading. Strength IS the signal; weakness
#     is what you avoid. Rises with RSI and only penalises a true blow-off
#     above ~92. Without this curve a stock ripping at RSI 86 scores 35 and
#     the technical pillar votes against exactly what the strategy hunts.
_OSC_CURVES = {
    'mean_reversion': (
        [0, 20, 30, 50, 65, 75, 85, 100],
        [90, 85, 75, 62, 72, 62, 35, 15],
    ),
    'momentum': (
        [0, 20, 30, 40, 50, 60, 70, 80, 88, 94, 100],
        [5, 12, 22, 35, 50, 65, 78, 88, 92, 78, 55],
    ),
}

_BB_CURVES = {
    # %B -> score. Mean reversion sells the upper band; momentum rides it.
    'mean_reversion': (
        [-0.3, 0.0, 0.2, 0.5, 0.8, 1.0, 1.3],
        [90, 85, 72, 60, 70, 45, 20],
    ),
    'momentum': (
        [-0.3, 0.0, 0.2, 0.5, 0.8, 1.0, 1.3],
        [10, 20, 35, 55, 78, 88, 72],
    ),
}


def osc_score(v, mode='mean_reversion'):
    """0-100 oscillator -> bullishness, read through the chosen strategy.

    Deliberately NOT `100 - v`: that punished every healthy uptrend (RSI 65
    scored 35) and fought the Momentum component.
    """
    xs, ys = _OSC_CURVES.get(mode) or _OSC_CURVES['mean_reversion']
    return float(np.interp(v, xs, ys))


def calculate_composite(info, piotroski, altman, macd_bb_data, rsi_data,
                         sharpe, sortino, rvol_data, hist_1y,
                         adx_data=None, stoch_data=None, obv_data=None,
                         mfi_data=None, willr_data=None,
                         weights=None, oscillator='mean_reversion'):
    """weights: pillar weights, defaults to DEFAULT_WEIGHTS. A pillar set to 0
    still gets computed and reported, it just does not move the final score --
    so you can see what a profile chose to ignore."""
    w = dict(DEFAULT_WEIGHTS, **(weights or {}))
    try:
        # --- Fundamental (28%) ---
        pe  = _num(info, 'trailingPE')
        pb  = _num(info, 'priceToBook')
        roe = _num(info, 'returnOnEquity')
        cr  = _num(info, 'currentRatio')
        de  = _num(info, 'debtToEquity')  # yfinance reports this in percent

        val_sc = None
        if pe is not None and pe > 0:
            val_sc = max(0, min(100, (50 - min(pe, 100)) / 50 * 100))
        if pb is not None and pb > 0:
            pb_sc = max(0, min(100, (5 - min(pb, 20)) / 5 * 100))
            val_sc = pb_sc if val_sc is None else (val_sc * 0.6 + pb_sc * 0.4)

        prof_sc = min(100, max(0, roe * 100 * 3.2)) if roe is not None else None

        hlth_parts = []
        if cr is not None and cr > 0:
            hlth_parts.append((min(100, cr / 3 * 100), 0.5))
        if de is not None:
            hlth_parts.append((max(0, min(100, 100 - de / 2)), 0.5))
        hlth_sc = _blend(hlth_parts)

        p_score = (piotroski['score'] / 9 * 100) if piotroski else None

        fund = _blend([
            (val_sc,  0.20),
            (prof_sc, 0.15),
            (hlth_sc, 0.15),
            (p_score, 0.50),
        ])

        if fund is not None:
            # EV/EBITDA bonus/penalty
            ev = _num(info, 'enterpriseToEbitda')
            if ev is not None and ev > 0:
                if ev < 8:
                    fund = min(100, fund + 5)
                elif ev > 15:
                    fund = max(0, fund - 5)

            # Dividend yield bonus
            dy_pct = dividend_yield_pct(info)
            if dy_pct is not None and dy_pct >= 4:
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

            # BB: 15% — %B can run outside [0,1]; clip before scoring.
            pct_b = min(1.3, max(-0.3, macd_bb_data['bb']['pct_b']))
            bb_xs, bb_ys = _BB_CURVES.get(oscillator) or _BB_CURVES['mean_reversion']
            bb_score = float(np.interp(pct_b, bb_xs, bb_ys))
            scores.append((bb_score, 0.15))

        if rsi_data:
            # RSI: 15%
            rsi_score = osc_score(rsi_data['value'], oscillator)
            scores.append((rsi_score, 0.15))

        if stoch_data:
            # Stochastic: 15%
            stoch_score = osc_score(stoch_data['k'], oscillator)
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
            # MFI: 5%
            scores.append((osc_score(mfi_data['value'], oscillator), 0.05))

        if willr_data:
            # Williams %R: 5% — -100..0 maps onto the same 0..100 axis as RSI
            scores.append((osc_score(willr_data['value'] + 100, oscillator), 0.05))

        tech = _blend(scores)

        # --- Risk (20%) ---
        risk = None
        if sharpe is not None:
            risk = max(0, min(80, 40 + sharpe * 15))
        if sortino is not None:
            sor  = max(0, min(80, 40 + sortino * 15))
            risk = sor if risk is None else (risk + sor) / 2
        if altman and risk is not None:
            if altman['zone'] == 'AMAN':
                risk = min(100, risk + 15)
            elif altman['zone'] == 'BAHAYA':
                risk = max(0, risk - 30)

        # --- Momentum (13%) ---
        mom = None
        if hist_1y is not None and len(hist_1y) > 126:
            try:
                h  = hist_1y['Close']
                m1 = (h.iloc[-1] / h.iloc[-22]  - 1) * 100
                m3 = (h.iloc[-1] / h.iloc[-66]  - 1) * 100
                m6 = (h.iloc[-1] / h.iloc[-126] - 1) * 100
                mom = max(0, min(100, 50 + m1 * 0.3 + m3 * 0.4 + m6 * 0.3))
            except Exception as e:
                print(f"Composite momentum error: {e}")

        # --- Sentiment (7%) ---
        sent = None
        if rvol_data:
            sent = max(0, min(90, 50 + (rvol_data['rvol'] - 1) * 20))
        rec    = (info.get('recommendationKey') or '').lower().replace('_', '')
        boosts = {'strongbuy': 20, 'buy': 10, 'hold': 0, 'neutral': 0, 'sell': -15, 'strongsell': -25}
        if rec in boosts:
            sent = max(0, min(100, (50 if sent is None else sent) + boosts[rec]))

        # Missing pillars drop out and their weight is redistributed, instead
        # of silently scoring 50 (which used to make a data-less bank look
        # like an average company).
        final = _blend([
            (fund, w['fundamental']), (tech, w['technical']), (risk, w['risk']),
            (mom, w['momentum']), (sent, w['sentiment']),
        ])
        if final is None:
            return None
        final = round(min(100, max(0, final)), 1)

        if final >= 70:   sig, cls = 'STRONG BUY',  'c-sb'
        elif final >= 60: sig, cls = 'BUY',          'c-b'
        elif final >= 45: sig, cls = 'HOLD',         'c-h'
        elif final >= 35: sig, cls = 'SELL',         'c-s'
        else:             sig, cls = 'STRONG SELL',  'c-ss'

        return {
            'final': final,
            'signal': sig,
            'cls': cls,
            'weights': w,
            'oscillator': oscillator,
            'components': {
                k: (round(v, 1) if v is not None else None)
                for k, v in (
                    ('Fundamental', fund), ('Technical', tech), ('Risk', risk),
                    ('Momentum', mom), ('Sentiment', sent),
                )
            },
        }
    except Exception as e:
        print(f"Composite error: {e}")
        return None
