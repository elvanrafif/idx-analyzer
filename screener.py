#!/usr/bin/env python3
"""Daily IDX screener -> Telegram, one run per day, several profiles at once.

Standalone: imports the same indicator functions the web analyzer uses, so a
BUY here and a BUY on the analyzer page can never disagree. Knows nothing
about Flask; the web app only reads what this writes.

    python3 screener.py
    python3 screener.py --dry-run              # no Telegram, print instead
    python3 screener.py --limit 20             # small universe, for testing
    python3 screener.py --profile gorengan     # one profile only

Five stages. Every stage is shared across profiles -- the expensive part is
fetching, so a ticker is fetched once and then scored under each profile that
wants it.

  1. universe   yf.screen every Indonesian equity              ~4 requests
  2. eligible   per-profile price/turnover/sector filters      0 requests
  3. prescreen  bulk OHLCV once, each profile's own gate       ~1 per 100
  4. analyse    fetch once, score N times                      ~6 per ticker
  5. report     save JSON + Telegram

Stage 3 is NOT the decision -- it only keeps stage 4 under Yahoo's rate limit.
calculate_composite makes the call, with that profile's weights and curve.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yfinance as yf
from dotenv import load_dotenv

from indicators.adx import calculate_adx
from indicators.altman_z import calculate_altman_z
from indicators.atr import calculate_atr
from indicators.composite import calculate_composite
from indicators.fundamental import is_financial
from indicators.key_levels import calculate_key_levels, calculate_outlook
from indicators.macd_bb import calculate_macd_bb
from indicators.mfi import calculate_mfi
from indicators.obv import calculate_obv
from indicators.piotroski import calculate_piotroski
from indicators.risk_metrics import calculate_sharpe, calculate_sortino
from indicators.rsi import calculate_rsi
from indicators.rvol import calculate_rvol
from indicators.sma import calculate_sma
from indicators.stochastic import calculate_stochastic
from indicators.williams_r import calculate_williams_r
from profiles import load as load_profiles
from services.yahoo_fetcher import fetch_ticker_data

load_dotenv()

WIB = timezone(timedelta(hours=7))
ROOT = Path(__file__).parent
RESULTS_DIR = ROOT / 'results'
STATUS_PATH = RESULTS_DIR / 'status.json'

BUY_SIGNALS = ('BUY', 'STRONG BUY')
BATCH = 100
SLEEP = float(os.environ.get('SCREENER_SLEEP', 0.7))
STALE_RUN_MIN = 45      # a status older than this is a crashed run, not a live one


def log(msg):
    print(f"[{datetime.now(WIB):%H:%M:%S}] {msg}", flush=True)


# ------------------------------------------------------------------- status

def write_status(**kw):
    """Progress for the web UI. A file, not memory: gunicorn runs 2 workers
    and the run happens in a third process entirely."""
    RESULTS_DIR.mkdir(exist_ok=True)
    kw.setdefault('updated', datetime.now(WIB).isoformat())
    try:
        STATUS_PATH.write_text(json.dumps(kw, default=str))
    except Exception as e:
        print(f"status write failed: {e}")


def read_status():
    try:
        return json.loads(STATUS_PATH.read_text())
    except Exception:
        return None


def run_in_progress():
    """True if another run is genuinely still going."""
    s = read_status()
    if not s or s.get('state') != 'running':
        return False
    try:
        age = datetime.now(WIB) - datetime.fromisoformat(s['updated'])
    except Exception:
        return False
    return age < timedelta(minutes=STALE_RUN_MIN)


# ------------------------------------------------------------- stage 1 + 2

def fetch_universe():
    if not hasattr(yf, 'screen') or not hasattr(yf, 'EquityQuery'):
        raise RuntimeError(
            f"yfinance {getattr(yf, '__version__', '?')} has no screen()/EquityQuery. "
            "Upgrade: pip install -U yfinance"
        )
    q = yf.EquityQuery('and', [
        yf.EquityQuery('eq', ['region', 'id']),
        yf.EquityQuery('gt', ['dayvolume', 1000]),
    ])
    seen, rows, offset = set(), [], 0
    while True:
        r = yf.screen(q, size=250, offset=offset,
                      sortField='dayvolume', sortAsc=False)
        quotes = r.get('quotes', [])
        if not quotes:
            break
        for x in quotes:
            sym = x.get('symbol')
            if sym and sym not in seen:
                seen.add(sym)
                rows.append(x)
        offset += len(quotes)
        if offset >= r.get('total', 0):
            break

    out = []
    for x in rows:
        price, volume = x.get('regularMarketPrice'), x.get('averageDailyVolume3Month')
        if not price or not volume:
            continue
        out.append({
            'ticker': x['symbol'].replace('.JK', ''),
            'symbol': x['symbol'],
            'name': x.get('shortName') or x.get('longName') or x['symbol'],
            'price': float(price),
            'turnover': float(price) * float(volume),
            'sector': x.get('sector'),
        })
    return out


def eligible_for(profile, universe, limit=None):
    """Stage 2 — the profile's own universe rules. No requests."""
    u = profile['universe']
    excl_sec = {s.lower() for s in (u.get('exclude_sectors') or [])}
    excl_tk = {t.upper() for t in (u.get('exclude_tickers') or [])}
    out = []
    for c in universe:
        if c['turnover'] < u['min_turnover']:
            continue
        if u.get('min_price') is not None and c['price'] < u['min_price']:
            continue
        if u.get('max_price') is not None and c['price'] > u['max_price']:
            continue
        if c['ticker'].upper() in excl_tk:
            continue
        if excl_sec and (c.get('sector') or '').lower() in excl_sec:
            continue
        out.append(c)
    out.sort(key=lambda d: -d['turnover'])
    return out[:limit] if limit else out


# ------------------------------------------------------------------ stage 3

def prescreen(symbols):
    """Bulk-download once and return {symbol: {'sma':…, 'rsi':…}} for the union
    of every profile's candidates. Gates are applied per profile afterwards."""
    bars_info = {}
    for i in range(0, len(symbols), BATCH):
        batch = symbols[i:i + BATCH]
        log(f"  bulk download {i + 1}-{i + len(batch)} of {len(symbols)}")
        write_status(state='running', stage='prescreen',
                     done=i + len(batch), total=len(symbols))
        df = yf.download(batch, period='1y', interval='1d', group_by='ticker',
                         threads=True, progress=False, auto_adjust=True)
        for sym in batch:
            try:
                bars = df[sym].dropna(subset=['Close'])
            except (KeyError, TypeError):
                continue
            if len(bars) < 60:
                continue
            sma, rsi = calculate_sma(bars), calculate_rsi(bars)
            if sma and rsi:
                bars_info[sym] = {'sma': sma, 'rsi': rsi,
                                  'rvol': rvol_recent(bars)}
        time.sleep(SLEEP)
    return bars_info


def rvol_recent(bars, days=5, window=20):
    """Highest relative volume over the last `days` bars.

    Not today's RVOL alone: a breakout that fired three days ago on heavy
    volume trades normally today, so a same-day check would reject exactly the
    setups it is meant to confirm. The question is "was there a volume surge
    recently", not "is there one right now".
    """
    vol = bars['Volume'].dropna()
    if len(vol) < window + days:
        return None
    # Baseline must END where the lookback window BEGINS. If the surge day sits
    # inside its own reference average it dilutes itself -- a genuine 4x spike
    # measured against a window containing it reads as only 3.5x.
    avg = float(vol.iloc[-(window + days):-days].mean())
    if avg <= 0:
        return None
    return round(max(float(vol.iloc[-k]) / avg for k in range(1, days + 1)), 2)


def passes_gate(profile, probe):
    g = profile.get('prescreen') or {}
    ema = g.get('above_ema')
    if ema == 50 and not probe['sma'].get('above_ema50'):
        return False
    if ema == 200 and not probe['sma'].get('above_ema200'):
        return False
    rsi_max = g.get('rsi_max')
    if rsi_max is not None and probe['rsi']['value'] >= rsi_max:
        return False
    min_rvol = g.get('min_rvol')
    if min_rvol is not None:
        # No volume behind the move = the classic false breakout. Reject before
        # spending a fetch on it, rather than merely docking a few points.
        rv = probe.get('rvol')
        if rv is None or rv < min_rvol:
            return False
    return True


# ------------------------------------------------------------------ stage 4

def indicator_set(data):
    """Every indicator, computed once. Nothing here depends on the profile —
    only the weighting downstream does."""
    info = data['info']
    return {
        'info': info,
        'rsi': calculate_rsi(data['hist_6m']),
        'sma': calculate_sma(data['hist_2y']),
        'adx': calculate_adx(data['hist_1y']),
        'macd_bb': calculate_macd_bb(data['hist_6m']),
        'stoch': calculate_stochastic(data['hist_3m']),
        'obv': calculate_obv(data['hist_1y']),
        'mfi': calculate_mfi(data['hist_3m']),
        'willr': calculate_williams_r(data['hist_3m']),
        'rvol': calculate_rvol(data['hist_3m']),
        'atr': calculate_atr(data['hist_6m']),
        'sharpe': calculate_sharpe(data['hist_1y']),
        'sortino': calculate_sortino(data['hist_1y']),
        'piotroski': calculate_piotroski(data['balance_sheet'], data['financials'],
                                         data['cashflow'], info),
        'altman': calculate_altman_z(data['balance_sheet'], data['financials'], info),
        'key_levels': calculate_key_levels(data['hist_3m']),
        'hist_1y': data['hist_1y'],
    }


def meets_requirements(profile, ind):
    """Hard prerequisites a profile declares, beyond the score itself."""
    req = profile.get('require') or []
    if 'fundamental_quality' in req:
        # Piotroski is the quality proof -- but it is undefined for banks and
        # insurers, so for those we accept a computable Fundamental pillar
        # instead. Demanding the F-Score outright would exclude every IDX bank.
        if not ind['piotroski'] and not is_financial(ind['info']):
            return False
    if 'piotroski' in req and not ind['piotroski']:
        return False
    if 'altman' in req and not ind['altman']:
        return False
    return True


def score_with(ind, profile):
    return calculate_composite(
        ind['info'], ind['piotroski'], ind['altman'], ind['macd_bb'], ind['rsi'],
        ind['sharpe'], ind['sortino'], ind['rvol'], ind['hist_1y'],
        adx_data=ind['adx'], stoch_data=ind['stoch'], obv_data=ind['obv'],
        mfi_data=ind['mfi'], willr_data=ind['willr'],
        weights=profile['weights'], oscillator=profile['oscillator'],
    )


def reasons_for(composite, ind, profile):
    """Two to four plain-language drivers, phrased for this profile."""
    out = []
    comp = composite.get('components') or {}
    w = composite.get('weights') or {}
    # Only rank pillars this profile actually counts -- quoting "Risk 90" on a
    # profile that weights risk at 0 would be a lie about why it scored.
    ranked = sorted(
        ((k, v) for k, v in comp.items()
         if v is not None and w.get(k.lower(), 0) > 0),
        key=lambda kv: -kv[1],
    )
    for name, val in ranked[:2]:
        if val >= 60:
            out.append(f"{name} {val:.0f}")

    adx = ind.get('adx')
    if adx and adx.get('strength') in ('STRONG', 'MODERATE'):
        if adx.get('direction') == 'BULLISH':
            out.append(f"ADX {adx['adx']:.0f} {adx['strength']} BULLISH")
        else:
            out.append(f"⚠ tren {adx['strength'].lower()} bearish")

    if profile['oscillator'] == 'momentum':
        rvol = ind.get('rvol')
        if rvol and rvol['rvol'] >= 2:
            out.append(f"RVOL {rvol['rvol']}x")
    else:
        sma = ind.get('sma')
        if sma and sma.get('cross_event'):
            out.append(sma['cross_event'].title())
        elif sma and sma.get('above_ema200'):
            out.append("harga > EMA200")

    if ind.get('rsi'):
        out.append(f"RSI {ind['rsi']['value']:.0f}")
    return out[:4]


def analyse(tickers, wanted_by, profiles, meta):
    """Fetch each ticker once, score it under every profile that wants it."""
    per_profile = {name: [] for name in profiles}
    failed = []
    total = len(tickers)
    for n, tk in enumerate(tickers, 1):
        write_status(state='running', stage='analyse', done=n, total=total,
                     ticker=tk)
        try:
            data = fetch_ticker_data(tk)
            if data is None:
                failed.append(tk)
                continue
            ind = indicator_set(data)
            info = ind['info']
            m = meta[tk]

            for name in wanted_by[tk]:
                p = profiles[name]
                if not meets_requirements(p, ind):
                    continue
                c = score_with(ind, p)
                if not c:
                    continue
                per_profile[name].append({
                    'ticker': tk,
                    'name': m['name'],
                    'sector': info.get('sector'),
                    'price': info.get('regularMarketPrice') or info.get('currentPrice'),
                    'turnover': m['turnover'],
                    'score': c['final'],
                    'signal': c['signal'],
                    'components': c.get('components'),
                    'outlook': calculate_outlook(ind['key_levels'], c, atr=ind['atr']),
                    'reasons': reasons_for(c, ind, p),
                })
            log(f"  [{n}/{total}] {tk} " + ' '.join(
                f"{name[:4]}={next((r['score'] for r in per_profile[name] if r['ticker'] == tk), '-')}"
                for name in wanted_by[tk]))
        except Exception as e:
            failed.append(tk)
            log(f"  [{n}/{total}] {tk} FAILED: {type(e).__name__}: {e}")
        time.sleep(SLEEP)
    return per_profile, failed


# ------------------------------------------------------------------ storage

def previous_run(before=None):
    if not RESULTS_DIR.exists():
        return None
    files = sorted((f for f in RESULTS_DIR.glob('*.json') if f.stem != 'status'),
                   reverse=True)
    for f in files:
        if before and f.stem >= before:
            continue
        try:
            return json.loads(f.read_text())
        except Exception as e:
            log(f"  skipping unreadable {f.name}: {e}")
    return None


def dropped_vs(prev, name, buys, analysed, profile):
    """Names that were BUY last run and are not now, with the reason.

    Flags a settings change explicitly: a stock can fall off the list because
    it weakened, or because you moved the threshold. Those are not the same
    thing and must not look the same.
    """
    if not prev:
        return []
    prev_block = (prev.get('profiles') or {}).get(name) or {}
    prev_buys = prev_block.get('buys') or []
    prev_settings = prev_block.get('settings') or {}
    settings_changed = (
        prev_settings.get('min_score') != profile['min_score']
        or prev_settings.get('min_turnover') != profile['universe']['min_turnover']
        or prev_settings.get('weights') != profile['weights']
    )
    now = {b['ticker'] for b in buys}
    scored = {r['ticker']: r for r in analysed}
    out = []
    for b in prev_buys:
        if b['ticker'] in now:
            continue
        cur = scored.get(b['ticker'])
        out.append({
            'ticker': b['ticker'],
            'prev_score': b.get('score'),
            'score': cur['score'] if cur else None,
            'signal': cur['signal'] if cur else 'tidak dianalisis',
            'settings_changed': settings_changed,
        })
    return out


def save_run(payload):
    """Merge into today's file rather than replace it.

    `--profile gorengan` used to overwrite the whole day, silently destroying
    the other three profiles' results. A partial run must only replace the
    blocks it actually recomputed.
    """
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{payload['date']}.json"
    if path.exists():
        try:
            old = json.loads(path.read_text())
            merged = dict(old.get('profiles') or {})
            merged.update(payload['profiles'])
            payload = dict(payload, profiles=merged,
                           partial_run=sorted(payload['profiles']))
        except Exception as e:
            log(f"  hasil lama tidak terbaca, ditimpa: {e}")
    path.write_text(json.dumps(payload, indent=2, default=str))
    return path


# ------------------------------------------------------------------ message

def format_message(payload):
    from services.notifier import esc, rp

    parts = [f"<b>📊 IDX Screener — {payload['date']}</b>",
             f"<i>{payload['universe']} emiten · {payload['analysed']} dianalisis "
             f"· {payload['elapsed_sec']}s</i>"]

    for name, block in payload['profiles'].items():
        buys, dropped = block['buys'], block['dropped']
        total = block.get('total_buys', len(buys))
        shown = f"{len(buys)} dari {total}" if total > len(buys) else str(total)
        head = (f"\n\n<b>━━ {esc(block['label']).upper()} ━━</b>\n"
                f"<i>{block['eligible']} lolos filter → {block['prescreened']} "
                f"lolos gate → {shown} BUY</i>")
        parts.append(head)

        if block.get('warn'):
            parts.append(f"\n<i>⚠ {esc(block['warn'])}</i>")

        if not buys:
            # NOT `continue`: an empty list is exactly when "what fell off"
            # matters most, so the dropped block below still has to run.
            parts.append("\nTidak ada yang lolos ambang.")

        for b in buys:
            o = b.get('outlook') or {}
            line = [f"\n<b>{esc(b['ticker'])}</b> · {esc(b['signal'])} <b>{b['score']}</b>",
                    f"{rp(b['price'])} · {esc(b.get('sector') or '—')}"]
            if o.get('entry_mid'):
                line.append(
                    f"E {rp(o['entry_low'])}–{rp(o['entry_high'])} · "
                    f"SL {rp(o['stop_loss'])} ({o['sl_pct']}%) · "
                    f"TP {rp(o['target1'])} (+{o['t1_pct']}%) · R:R {o['rr_ratio']}")
            if b.get('reasons'):
                line.append(f"<i>{esc(' · '.join(b['reasons']))}</i>")
            parts.append('\n'.join(line))

        if dropped:
            note = ' <i>(setelan berubah)</i>' if dropped[0].get('settings_changed') else ''
            items = ', '.join(
                f"{esc(d['ticker'])} ({d['score'] if d['score'] is not None else '—'})"
                for d in dropped)
            parts.append(f"\n<b>Keluar:</b>{note} {items}")

    if payload.get('failed'):
        parts.append(f"\n\n<i>{len(payload['failed'])} emiten gagal diambil datanya.</i>")
    return '\n'.join(parts)


# --------------------------------------------------------------------- main

def run(limit=None, dry_run=False, only=None):
    started = datetime.now(WIB)
    profiles = load_profiles()
    if only:
        missing = [n for n in only if n not in profiles]
        if missing:
            raise SystemExit(f"profil tidak dikenal: {missing}. Ada: {list(profiles)}")
        profiles = {n: profiles[n] for n in only}

    write_status(state='running', stage='universe', started=started.isoformat(),
                 profiles=list(profiles))
    log(f"stage 1: universe ({len(profiles)} profil: {', '.join(profiles)})")
    universe = fetch_universe()
    log(f"  {len(universe)} emiten")

    log("stage 2: filter per profil")
    eligible = {}
    for name, p in profiles.items():
        eligible[name] = eligible_for(p, universe, limit)
        log(f"  {name:<9} {len(eligible[name])} lolos filter universe")

    # One bulk download for the union, not one per profile.
    union = {c['symbol']: c for lst in eligible.values() for c in lst}
    log(f"stage 3: prescreen {len(union)} unik (gabungan semua profil)")
    probes = prescreen(list(union))

    survivors, wanted_by = {}, {}
    for name, p in profiles.items():
        keep = [c for c in eligible[name]
                if c['symbol'] in probes and passes_gate(p, probes[c['symbol']])]
        survivors[name] = keep
        for c in keep:
            wanted_by.setdefault(c['ticker'], []).append(name)
        log(f"  {name:<9} {len(keep)} lolos gate")

    meta = {c['ticker']: c for lst in eligible.values() for c in lst}
    tickers = sorted(wanted_by, key=lambda t: -meta[t]['turnover'])
    log(f"stage 4: analisis {len(tickers)} emiten unik "
        f"(vs {sum(len(v) for v in survivors.values())} kalau tiap profil jalan sendiri)")
    per_profile, failed = analyse(tickers, wanted_by, profiles, meta)

    write_status(state='running', stage='report', done=len(tickers), total=len(tickers))
    prev = previous_run(before=started.strftime('%Y-%m-%d'))
    blocks = {}
    for name, p in profiles.items():
        rows = per_profile[name]
        qualified = sorted((r for r in rows
                            if r['signal'] in BUY_SIGNALS and r['score'] >= p['min_score']),
                           key=lambda r: -r['score'])
        cap = p.get('max_results', 40)
        buys = qualified[:cap]
        # Never let a cap read as "that's all there was". 40 shown out of 63
        # qualifying is a different fact from 40 qualifying.
        if len(qualified) > len(buys):
            log(f"  {name}: {len(qualified)} lolos, ditampilkan {len(buys)} (max_results)")
        blocks[name] = {
            'label': p['label'],
            'desc': p.get('desc'),
            'warn': p.get('warn'),
            'eligible': len(eligible[name]),
            'prescreened': len(survivors[name]),
            'analysed': len(rows),
            'buys': buys,
            'total_buys': len(qualified),
            'dropped': dropped_vs(prev, name, buys, rows, p),
            'settings': {
                'min_score': p['min_score'],
                'min_turnover': p['universe']['min_turnover'],
                'min_price': p['universe'].get('min_price'),
                'max_price': p['universe'].get('max_price'),
                'weights': p['weights'],
                'oscillator': p['oscillator'],
                'prescreen': p['prescreen'],
            },
        }

    payload = {
        'date': started.strftime('%Y-%m-%d'),
        'run_at': started.isoformat(),
        'universe': len(universe),
        'analysed': len(tickers),
        'failed': failed,
        'elapsed_sec': round((datetime.now(WIB) - started).total_seconds()),
        'profiles': blocks,
    }
    path = save_run(payload)
    log(f"saved {path}")

    message = format_message(payload)
    if dry_run:
        print('\n--- TELEGRAM (dry run) ---\n')
        print(message)
    else:
        from services.notifier import send, NotifierNotConfigured
        try:
            log(f"telegram: {send(message)} message(s) sent")
        except NotifierNotConfigured as e:
            log(f"telegram skipped: {e}")
        except Exception as e:
            log(f"telegram FAILED: {e}")

    write_status(state='done', stage='done', date=payload['date'],
                 elapsed_sec=payload['elapsed_sec'],
                 buys={n: len(b['buys']) for n, b in blocks.items()})
    log(f"done in {payload['elapsed_sec']}s — " +
        ', '.join(f"{n} {len(b['buys'])}" for n, b in blocks.items()))
    return payload


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true', help="print instead of sending")
    p.add_argument('--limit', type=int, help="cap each profile's universe (testing)")
    p.add_argument('--profile', action='append', help="run only this profile (repeatable)")
    p.add_argument('--force', action='store_true', help="ignore a running-run lock")
    a = p.parse_args()

    if not a.force and run_in_progress():
        log("run lain sedang berjalan; pakai --force kalau yakin itu sisa crash")
        sys.exit(1)
    try:
        run(limit=a.limit, dry_run=a.dry_run, only=a.profile)
    except KeyboardInterrupt:
        write_status(state='error', stage='interrupted')
        log("interrupted")
        sys.exit(130)
    except Exception as e:
        write_status(state='error', stage='failed', error=f"{type(e).__name__}: {e}")
        raise


if __name__ == '__main__':
    main()
