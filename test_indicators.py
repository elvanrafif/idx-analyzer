"""Runnable checks for the indicator maths. `python3 test_indicators.py`

Deliberately no fixtures/framework: synthetic frames with known answers, so
each assert fails loudly if the formula regresses.
"""
import numpy as np
import pandas as pd

from indicators.composite import osc_score, _blend, calculate_composite
from indicators.fundamental import calculate_dividend_yield, dividend_yield_pct, is_financial
from indicators.key_levels import calculate_key_levels, calculate_outlook, idx_tick
from indicators.macd_bb import calculate_macd_bb
from indicators.piotroski import get_line_item
from indicators.risk_metrics import calculate_sortino
from indicators.rsi import calculate_rsi
from indicators.rvol import calculate_rvol, session_fraction
from indicators.sma import calculate_sma
from indicators.williams_r import calculate_williams_r
from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))


def _frame(closes, volumes=None):
    closes = np.asarray(closes, dtype=float)
    idx = pd.date_range('2024-01-01', periods=len(closes), freq='B', tz=WIB)
    return pd.DataFrame({
        'Open': closes,
        'High': closes * 1.01,
        'Low': closes * 0.99,
        'Close': closes,
        'Volume': volumes if volumes is not None else np.full(len(closes), 1000.0),
    }, index=idx)


def test_dividend_yield_units():
    # yfinance >= 0.2.52 reports dividendYield in percent, not as a fraction
    assert dividend_yield_pct({'dividendYield': 5.65}) == 5.65
    # legacy fraction form still handled
    assert abs(dividend_yield_pct({'dividendYield': 0.0446}) - 4.46) < 1e-9
    assert dividend_yield_pct({'dividendYield': None}) is None
    # trailing wins over the forward/indicated figure (real UNVR numbers)
    unvr = {'dividendYield': 12.81, 'trailingAnnualDividendYield': 0.064044945}
    assert abs(dividend_yield_pct(unvr) - 6.4044945) < 1e-6
    d = calculate_dividend_yield(unvr)
    assert d['yield_pct'] == 6.4 and d['forward_pct'] == 12.81, d
    assert d['signal'] == 'MENARIK', d


def test_is_financial():
    assert is_financial({'sector': 'Financial Services', 'industry': 'Banks - Regional'})
    assert is_financial({'sector': 'X', 'industry': 'Insurance - Life'})
    assert not is_financial({'sector': 'Consumer Defensive', 'industry': 'Tobacco'})
    assert not is_financial(None)


def test_rsi_known_value():
    # Monotone rise => avg_loss 0 => RSI pinned at 100
    up = _frame(np.arange(100, 140, dtype=float))
    assert calculate_rsi(up)['value'] == 100.0
    down = _frame(np.arange(140, 100, -1, dtype=float))
    assert calculate_rsi(down)['value'] == 0.0


def test_williams_r_bounds():
    f = _frame(np.linspace(100, 200, 60))
    w = calculate_williams_r(f)
    assert -100 <= w['value'] <= 0, w
    # closing at the top of the range => %R near 0 (overbought)
    assert w['signal'] == 'OVERBOUGHT', w


def test_bollinger_population_std():
    f = _frame(100 + np.sin(np.arange(200) / 5) * 10)
    bb = calculate_macd_bb(f)['bb']
    c = f['Close']
    expect = float((c.rolling(20).mean() + 2 * c.rolling(20).std(ddof=0)).iloc[-1])
    assert abs(bb['upper'] - round(expect, 0)) < 1.0, (bb['upper'], expect)
    # squeeze is now a percentile, so it carries a rank
    assert bb['bw_rank'] is not None and 0 <= bb['bw_rank'] <= 1


def test_sortino_uses_full_sample():
    rng = np.random.default_rng(0)
    closes = 1000 * np.cumprod(1 + rng.normal(0.0005, 0.02, 300))
    f = _frame(closes)
    got = calculate_sortino(f)

    ret = f['Close'].pct_change().dropna()
    rf = 0.065
    shortfall = np.minimum(ret - rf / 252, 0)
    dd = float(np.sqrt((shortfall ** 2).mean()) * np.sqrt(252))
    expect = round((ret.mean() * 252 - rf) / dd, 3)
    assert got == expect, (got, expect)

    # and it must differ from the naive ret[ret<0].std() version
    naive_dd = float(ret[ret < 0].std() * np.sqrt(252))
    assert abs(dd - naive_dd) > 1e-6


def test_ema200_needs_full_span():
    assert calculate_sma(_frame(np.linspace(100, 200, 150)))['ema200'] is None
    long = calculate_sma(_frame(np.linspace(100, 200, 400)))
    assert long['ema200'] is not None and long['golden_cross'] is True


def test_pivots_exclude_current_bar():
    closes = np.array([100.0] * 10 + [500.0])  # today is a wild outlier
    kl = calculate_key_levels(_frame(closes))
    # today's 500 must not leak into the pivot built from prior bars
    assert kl['pivot'] < 120, kl
    assert kl['current'] == 500


def test_idx_tick_snapping():
    assert idx_tick(150) == 1 and idx_tick(300) == 2
    assert idx_tick(1500) == 5 and idx_tick(3000) == 10 and idx_tick(9000) == 25
    kl = calculate_key_levels(_frame(np.linspace(3000, 3100, 30)))
    for k in ('pivot', 'r1', 's1', 'current'):
        assert kl[k] % 10 == 0, (k, kl[k])


def test_outlook_rr_uses_one_denominator():
    kl = calculate_key_levels(_frame(np.linspace(3000, 3100, 30)))
    o = calculate_outlook(kl, {'final': 70}, atr={'value': 50.0, 'pct': 1.6})
    expect_sl = abs((o['entry_mid'] - o['stop_loss']) / o['entry_mid'] * 100)
    assert abs(o['sl_pct'] - round(expect_sl, 1)) < 0.11, o
    expect_rr = round(o['t1_pct'] / o['sl_pct'], 1)
    assert o['rr_ratio'] == expect_rr, o


def test_rvol_prorates_partial_session():
    vols = np.full(30, 1000.0)
    vols[-1] = 500.0  # half a day's worth
    f = _frame(np.full(30, 100.0), volumes=vols)
    today = f.index[-1].to_pydatetime()

    midday = today.replace(hour=11, minute=30)   # 150 of 240 session minutes
    mid = calculate_rvol(f, now=midday)
    assert mid['partial'] is True
    assert abs(mid['rvol'] - (500 / (150 / 240)) / 1000) < 0.01, mid

    after = today.replace(hour=16, minute=0)
    close = calculate_rvol(f, now=after)
    assert close['partial'] is False and close['rvol'] == 0.5, close

    assert session_fraction(today.replace(hour=8, minute=0)) == 1.0
    assert session_fraction(today.replace(hour=12, minute=0)) == 150 / 240


def test_osc_score_does_not_punish_healthy_trend():
    assert osc_score(65) > osc_score(50)      # trending beats drifting
    assert osc_score(25) > osc_score(50)      # oversold is an opportunity
    assert osc_score(90) < 40                 # genuinely extended
    assert osc_score(65) > 100 - 65           # the old `100 - v` inversion


def test_blend_renormalises():
    assert _blend([(80, 0.5), (None, 0.5)]) == 80
    assert _blend([(None, 1.0)]) is None
    assert abs(_blend([(100, 0.25), (0, 0.75)]) - 25) < 1e-9


def test_composite_drops_missing_pillars():
    f = _frame(np.linspace(1000, 1200, 300))
    bank = {'sector': 'Financial Services', 'industry': 'Banks - Regional'}
    c = calculate_composite(bank, None, None, None, None, None, None, None, f)
    assert c is not None
    assert c['components']['Fundamental'] is None, c['components']
    assert c['components']['Momentum'] is not None
    # no fake 50s dragging the score to the middle
    assert c['final'] == round(c['components']['Momentum'], 1), c


def test_line_item_prefers_exact_label():
    df = pd.DataFrame(
        {'2024': [999.0, 111.0]},
        index=['Net Income Continuous Operations', 'Net Income'],
    )
    assert get_line_item(df, 0, 'net income') == 111.0


if __name__ == '__main__':
    for name, fn in sorted(list(globals().items())):
        if name.startswith('test_'):
            fn()
            print(f"ok  {name}")
    print("\nall checks passed")
