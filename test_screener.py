"""Checks for the screener's pure logic. `python3 test_screener.py`

Network stages (universe/prescreen/analyse) are not covered here -- they are
exercised by `python3 screener.py --limit 12 --dry-run`.
"""
import copy

from indicators.composite import calculate_composite, osc_score
from profiles import BUILTIN, load, validate
import screener as scr
from screener import (dropped_vs, eligible_for, format_message,
                      meets_requirements, passes_gate, reasons_for)
from services.notifier import _split, esc, rp

CHUNK_LIMIT = 3800
P = load()


# ── fixtures ────────────────────────────────────────────────────────────────

def _buy(ticker='ANTM', score=68.2, **over):
    b = {
        'ticker': ticker, 'name': 'ANTAM (Persero) Tbk.', 'sector': 'Basic Materials',
        'price': 3130, 'score': score, 'signal': 'BUY',
        'reasons': ['Fundamental 82', 'RSI 58'],
        'outlook': {
            'entry_low': 2950, 'entry_high': 3140, 'entry_mid': 3040,
            'stop_loss': 2820, 'sl_pct': 7.2,
            'target1': 3140, 't1_pct': 3.3, 'rr_ratio': 0.5,
        },
    }
    b.update(over)
    return b


def _block(label='Default', buys=(), dropped=(), **over):
    b = {
        'label': label, 'desc': 'desc', 'warn': None,
        'eligible': 146, 'prescreened': 83, 'analysed': 83,
        'buys': list(buys), 'total_buys': len(buys), 'dropped': list(dropped),
        'settings': {'min_score': 60, 'min_turnover': 10e9,
                     'weights': dict(BUILTIN['default']['weights']),
                     'oscillator': 'mean_reversion'},
    }
    b.update(over)
    return b


def _payload(profiles=None, **over):
    p = {
        'date': '2026-08-20', 'universe': 822, 'analysed': 238,
        'failed': [], 'elapsed_sec': 640,
        'profiles': profiles if profiles is not None else {'default': _block()},
    }
    p.update(over)
    return p


# ── formatting ──────────────────────────────────────────────────────────────

def test_rupiah_uses_indonesian_separator():
    assert rp(3130) == 'Rp 3.130'
    assert rp(1234567) == 'Rp 1.234.567'
    assert rp(None) == '—'


def test_message_has_a_section_per_profile():
    msg = format_message(_payload({
        'default': _block('Default', [_buy('ANTM')]),
        'gorengan': _block('Gorengan', [_buy('MDIA', 78.6)], warn='hati-hati'),
    }))
    assert '━━ DEFAULT ━━' in msg and '━━ GORENGAN ━━' in msg
    assert '<b>ANTM</b>' in msg and '<b>MDIA</b>' in msg
    assert 'hati-hati' in msg, "a profile warning must reach the message"


def test_message_discloses_a_truncated_list():
    # 40 shown out of 63 qualifying is a different fact from 40 qualifying.
    msg = format_message(_payload({'default': _block(
        buys=[_buy(f'T{i:02d}') for i in range(40)], total_buys=63)}))
    assert '40 dari 63 BUY' in msg, msg[:400]
    # and when nothing was cut, no confusing "N dari N"
    msg = format_message(_payload({'default': _block(buys=[_buy()])}))
    assert '1 BUY' in msg and 'dari' not in msg.split('━━')[1]


def test_message_handles_empty_and_dropped():
    msg = format_message(_payload({'default': _block()}))
    assert 'Tidak ada yang lolos ambang.' in msg

    msg = format_message(_payload({'default': _block(
        dropped=[{'ticker': 'TLKM', 'prev_score': 61.2, 'score': 54.0,
                  'settings_changed': False}])}))
    assert 'Keluar:' in msg and 'TLKM (54.0)' in msg
    assert 'setelan berubah' not in msg

    # a stock that fell off because the THRESHOLD moved must say so
    msg = format_message(_payload({'default': _block(
        dropped=[{'ticker': 'TLKM', 'prev_score': 61.2, 'score': 60.9,
                  'settings_changed': True}])}))
    assert 'setelan berubah' in msg


def test_message_survives_missing_outlook():
    msg = format_message(_payload({'default': _block(buys=[_buy(outlook=None)])}))
    assert '<b>ANTM</b>' in msg and 'SL ' not in msg


def test_failed_tickers_are_reported_not_hidden():
    msg = format_message(_payload({'default': _block(buys=[_buy()])},
                                  failed=['AAAA', 'BBBB']))
    assert '2 emiten gagal' in msg


def test_html_is_escaped():
    msg = format_message(_payload({'default': _block(
        buys=[_buy(sector='Oil <b>&</b> Gas')])}))
    assert '&lt;b&gt;' in msg and '<b>Oil' not in msg
    assert esc('a & b') == 'a &amp; b'


def test_split_keeps_stock_blocks_whole():
    blocks = [f"<b>TK{i:03d}</b> · BUY 60\nRp 1.000\nEntry x" for i in range(200)]
    parts = _split('\n\n'.join(blocks))
    assert len(parts) > 1
    for p in parts:
        assert len(p) <= CHUNK_LIMIT
    joined = '\n\n'.join(parts)
    for b in blocks:
        assert b in joined


def test_split_short_text_stays_one_message():
    assert _split('halo') == ['halo']


# ── oscillator curves ───────────────────────────────────────────────────────

def test_momentum_curve_inverts_the_mean_reversion_verdict():
    # The whole reason profiles need a curve and not just weights.
    assert osc_score(86, 'mean_reversion') < 40
    assert osc_score(86, 'momentum') > 85
    # momentum must rise with strength up to the blow-off, then fall
    assert osc_score(50, 'momentum') < osc_score(70, 'momentum') < osc_score(88, 'momentum')
    assert osc_score(100, 'momentum') < osc_score(88, 'momentum')
    # and weakness is NOT an opportunity in momentum mode
    assert osc_score(25, 'momentum') < osc_score(25, 'mean_reversion')
    # unknown mode must not explode, it falls back
    assert osc_score(50, 'nonsense') == osc_score(50, 'mean_reversion')


def test_weights_change_the_score():
    kw = dict(info={'trailingPE': 12.0, 'returnOnEquity': 0.2},
              piotroski={'score': 7}, altman=None, macd_bb_data=None,
              rsi_data={'value': 86.0}, sharpe=None, sortino=None,
              rvol_data=None, hist_1y=None)
    tech_heavy = calculate_composite(
        **kw, weights={'fundamental': 0, 'technical': 1, 'risk': 0,
                       'momentum': 0, 'sentiment': 0})
    fund_heavy = calculate_composite(
        **kw, weights={'fundamental': 1, 'technical': 0, 'risk': 0,
                       'momentum': 0, 'sentiment': 0})
    assert tech_heavy['final'] != fund_heavy['final']
    # RSI 86 read two ways, everything else held constant
    mr = calculate_composite(**kw, weights={'fundamental': 0, 'technical': 1,
                                            'risk': 0, 'momentum': 0, 'sentiment': 0},
                             oscillator='mean_reversion')
    mo = calculate_composite(**kw, weights={'fundamental': 0, 'technical': 1,
                                            'risk': 0, 'momentum': 0, 'sentiment': 0},
                             oscillator='momentum')
    assert mo['final'] > mr['final'], (mo['final'], mr['final'])
    assert mo['oscillator'] == 'momentum'


def test_zero_weight_pillar_is_reported_but_ignored():
    c = calculate_composite(
        info={'trailingPE': 12.0}, piotroski={'score': 9}, altman=None,
        macd_bb_data=None, rsi_data={'value': 60.0}, sharpe=None, sortino=None,
        rvol_data=None, hist_1y=None,
        weights={'fundamental': 0, 'technical': 1, 'risk': 0,
                 'momentum': 0, 'sentiment': 0})
    assert c['components']['Fundamental'] is not None, "still computed, for display"
    assert abs(c['final'] - c['components']['Technical']) < 0.11, "but must not move the score"


# ── profiles ────────────────────────────────────────────────────────────────

def test_builtin_profiles_all_validate():
    for name, p in load().items():
        validate(p, name)
    assert set(load()) == {'default', 'value', 'breakout', 'gorengan'}


def test_validation_rejects_nonsense():
    bad = [
        ({'weights': {k: 0 for k in ('fundamental', 'technical', 'risk',
                                     'momentum', 'sentiment')},
          'oscillator': 'momentum'}, 'bobot nol'),
        ({'weights': dict(BUILTIN['default']['weights']), 'oscillator': 'x'}, 'oscillator'),
        ({'weights': dict(BUILTIN['default']['weights']), 'oscillator': 'momentum',
          'min_score': 150}, 'min_score'),
        ({'weights': dict(BUILTIN['default']['weights']), 'oscillator': 'momentum',
          'universe': {'min_price': 900, 'max_price': 100}}, 'harga terbalik'),
    ]
    for cfg, why in bad:
        try:
            validate(cfg, 'x')
            raise AssertionError(f"tidak ditolak: {why}")
        except ValueError:
            pass


def test_universe_filters():
    uni = [
        {'ticker': 'AAA', 'symbol': 'AAA.JK', 'price': 50, 'turnover': 20e9, 'sector': 'Energy'},
        {'ticker': 'BBB', 'symbol': 'BBB.JK', 'price': 3000, 'turnover': 20e9, 'sector': 'Energy'},
        {'ticker': 'CCC', 'symbol': 'CCC.JK', 'price': 300, 'turnover': 1e9, 'sector': 'Energy'},
        {'ticker': 'DDD', 'symbol': 'DDD.JK', 'price': 300, 'turnover': 20e9, 'sector': 'Financial Services'},
    ]
    got = {c['ticker'] for c in eligible_for(P['gorengan'], uni)}
    assert got == {'AAA', 'DDD'}, got   # BBB too pricey, CCC too illiquid

    p = copy.deepcopy(P['gorengan'])
    p['universe']['exclude_sectors'] = ['Financial Services']
    assert {c['ticker'] for c in eligible_for(p, uni)} == {'AAA'}

    p['universe']['exclude_sectors'] = []
    p['universe']['exclude_tickers'] = ['aaa']    # case-insensitive
    assert {c['ticker'] for c in eligible_for(p, uni)} == {'DDD'}


def test_prescreen_gate_respects_profile():
    below = {'sma': {'above_ema50': False, 'above_ema200': False}, 'rsi': {'value': 50.0}}
    ripping = {'sma': {'above_ema50': True, 'above_ema200': True}, 'rsi': {'value': 86.0}}

    assert not passes_gate(P['default'], below)
    assert not passes_gate(P['default'], ripping), "RSI 86 exceeds default's 78 ceiling"
    assert passes_gate(P['gorengan'], ripping), "gorengan must let a runner through"
    # value has no EMA gate: a cheap company under its EMA50 is the point
    assert passes_gate(P['value'], below)


def test_value_profile_admits_banks_but_demands_quality_elsewhere():
    bank = {'info': {'sector': 'Financial Services', 'industry': 'Banks - Regional'},
            'piotroski': None, 'altman': None}
    plain_no_fscore = {'info': {'sector': 'Energy', 'industry': 'Coal'},
                       'piotroski': None, 'altman': None}
    plain_with = dict(plain_no_fscore, piotroski={'score': 7})

    assert meets_requirements(P['value'], bank), \
        "Piotroski is undefined for banks; requiring it would exclude every IDX bank"
    assert not meets_requirements(P['value'], plain_no_fscore)
    assert meets_requirements(P['value'], plain_with)
    # profiles without the requirement take anything
    assert meets_requirements(P['gorengan'], plain_no_fscore)


def test_reasons_only_cite_pillars_the_profile_counts():
    ind = {'adx': {'adx': 31.0, 'strength': 'STRONG', 'direction': 'BULLISH'},
           'sma': {'above_ema200': True, 'cross_event': None},
           'rsi': {'value': 58.4}, 'rvol': {'rvol': 3.1}}
    comp = {'components': {'Fundamental': 82.0, 'Technical': 61.0, 'Risk': 90.0,
                           'Momentum': None, 'Sentiment': 55.0},
            'weights': dict(BUILTIN['gorengan']['weights'])}
    r = reasons_for(comp, ind, P['gorengan'])
    assert not any('Risk' in x for x in r), \
        "gorengan weights risk at 0; quoting Risk 90 would misstate why it scored"
    assert not any('Fundamental' in x for x in r)
    assert any('RVOL 3.1x' in x for x in r), "momentum profiles should surface volume"

    comp_def = dict(comp, weights=dict(BUILTIN['default']['weights']))
    r = reasons_for(comp_def, ind, P['default'])
    assert r[0] == 'Risk 90'
    assert 'harga > EMA200' in r


def test_reasons_flag_bearish_trend_instead_of_praising_it():
    ind = {'adx': {'adx': 22.0, 'strength': 'MODERATE', 'direction': 'BEARISH'},
           'sma': {'above_ema200': False, 'cross_event': None},
           'rsi': {'value': 58.4}, 'rvol': None}
    comp = {'components': {'Technical': 61.0},
            'weights': dict(BUILTIN['default']['weights'])}
    r = reasons_for(comp, ind, P['default'])
    assert not any('MODERATE BEARISH' in x for x in r), r
    assert any('⚠' in x and 'bearish' in x for x in r), r
    # nothing here may crash on missing indicators
    assert isinstance(reasons_for({'components': {}, 'weights': {}},
                                  {'adx': None, 'sma': None, 'rsi': None, 'rvol': None},
                                  P['default']), list)


def test_dropped_marks_a_settings_change():
    prev = {'profiles': {'default': {
        'buys': [{'ticker': 'TLKM', 'score': 61.0}],
        'settings': {'min_score': 60, 'min_turnover': 10e9,
                     'weights': dict(BUILTIN['default']['weights'])}}}}
    analysed = [{'ticker': 'TLKM', 'score': 60.5, 'signal': 'BUY'}]

    same = dropped_vs(prev, 'default', [], analysed, P['default'])
    assert same[0]['ticker'] == 'TLKM' and same[0]['settings_changed'] is False

    stricter = copy.deepcopy(P['default'])
    stricter['min_score'] = 65
    moved = dropped_vs(prev, 'default', [], analysed, stricter)
    assert moved[0]['settings_changed'] is True, \
        "fell off because the bar moved, not because it weakened"

    assert dropped_vs(None, 'default', [], analysed, P['default']) == []


def test_partial_run_does_not_destroy_other_profiles(tmp=None):
    """`--profile gorengan` must not wipe the other three from today's file."""
    import json
    import tempfile
    from pathlib import Path

    original = scr.RESULTS_DIR
    try:
        scr.RESULTS_DIR = Path(tempfile.mkdtemp())
        full = _payload({'default': _block('Default', [_buy('ANTM')]),
                         'gorengan': _block('Gorengan', [_buy('MDIA')])})
        scr.save_run(full)

        partial = _payload({'gorengan': _block('Gorengan', [_buy('BEEF', 80.0)])})
        path = scr.save_run(partial)

        saved = json.loads(path.read_text())
        assert set(saved['profiles']) == {'default', 'gorengan'}, saved['profiles']
        assert saved['profiles']['default']['buys'][0]['ticker'] == 'ANTM'
        assert saved['profiles']['gorengan']['buys'][0]['ticker'] == 'BEEF'
        assert saved['partial_run'] == ['gorengan']
    finally:
        scr.RESULTS_DIR = original


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_'):
            fn()
            print(f"ok  {name}")
    print("\nall screener checks passed")
