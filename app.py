import hmac
import json
import math
import os
from datetime import datetime
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from services.yahoo_fetcher import fetch_ticker_data, df_to_dict
from services.ai_analyzer import get_all_insights, test_connection
from indicators.piotroski import calculate_piotroski
from indicators.altman_z import calculate_altman_z
from indicators.macd_bb import calculate_macd_bb
from indicators.rsi import calculate_rsi
from indicators.sma import calculate_sma
from indicators.rvol import calculate_rvol
from indicators.risk_metrics import calculate_sharpe, calculate_sortino, calculate_fcf_yield
from indicators.composite import calculate_composite
from indicators.key_levels import calculate_key_levels, calculate_outlook
from indicators.adx import calculate_adx
from indicators.avwap import calculate_avwap
from indicators.stochastic import calculate_stochastic
from indicators.obv import calculate_obv
from indicators.atr import calculate_atr
from indicators.mfi import calculate_mfi
from indicators.williams_r import calculate_williams_r
from indicators.fundamental import calculate_dividend_yield, calculate_ev_ebitda

load_dotenv()
app = Flask(__name__)
# Profiles carry a deliberate display order (default, value, breakout,
# gorengan). Flask sorts JSON keys by default, which silently reordered the
# screener tabs alphabetically.
app.json.sort_keys = False


def clean_nan(obj):
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze')
def analyze():
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({"error": "Ticker cannot be empty."})

    try:
        data = fetch_ticker_data(ticker)
        if data is None:
            return jsonify({"error": f"Ticker {ticker} not found on IDX (Indonesia Stock Exchange)."})

        info = data['info']
        bs = data['balance_sheet']
        fs = data['financials']
        cf = data['cashflow']

        sharpe = calculate_sharpe(data['hist_1y'])
        sortino = calculate_sortino(data['hist_1y'])
        piotroski = calculate_piotroski(bs, fs, cf, info)
        altman = calculate_altman_z(bs, fs, info)
        macd_bb = calculate_macd_bb(data['hist_6m'])
        rsi = calculate_rsi(data['hist_6m'])
        sma = calculate_sma(data['hist_2y'])
        rvol = calculate_rvol(data['hist_3m'])
        fcf_yield = calculate_fcf_yield(info)

        adx = calculate_adx(data['hist_1y'])   # ADX needs ~150 bars to converge
        avwap = calculate_avwap(data['hist_3m'])
        stochastic = calculate_stochastic(data['hist_3m'])
        obv = calculate_obv(data['hist_1y'])
        atr        = calculate_atr(data['hist_6m'])
        mfi        = calculate_mfi(data['hist_3m'])
        williams_r = calculate_williams_r(data['hist_3m'])
        div_yield  = calculate_dividend_yield(info)
        ev_ebitda  = calculate_ev_ebitda(info)

        composite = calculate_composite(
            info, piotroski, altman, macd_bb, rsi,
            sharpe, sortino, rvol, data['hist_1y'],
            adx_data=adx, stoch_data=stochastic, obv_data=obv,
            mfi_data=mfi, willr_data=williams_r,
        )

        key_levels = calculate_key_levels(data['hist_3m'])
        outlook = calculate_outlook(key_levels, composite, atr=atr)

        return jsonify(clean_nan({
            "ticker": ticker,
            "updated": data['updated'],
            "info": info,
            "financials": df_to_dict(fs),
            "balance_sheet": df_to_dict(bs),
            "cashflow": df_to_dict(cf),
            "quarterly": df_to_dict(data['quarterly']),
            "piotroski": piotroski,
            "altman": altman,
            "macd_bb": macd_bb,
            "rsi": rsi,
            "sma": sma,
            "rvol": rvol,
            "adx": adx,
            "avwap": avwap,
            "stochastic": stochastic,
            "obv": obv,
            "atr":        atr,
            "mfi":        mfi,
            "williams_r": williams_r,
            "div_yield":  div_yield,
            "ev_ebitda":  ev_ebitda,
            "fcf_yield": fcf_yield,
            "sharpe": sharpe,
            "sortino": sortino,
            "composite": composite,
            "key_levels": key_levels,
            "outlook": outlook,
        }))
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": f"Technical error: {str(e)}"})


# ── Screener ──
# The app reads what screener.py wrote and can kick off a run, but never does
# the screening inside a request: it takes minutes and fires hundreds of Yahoo
# calls, far past any gunicorn timeout. A trigger spawns a detached process and
# returns immediately; progress is tracked through results/status.json so it
# survives being read by a different gunicorn worker than the one that started it.
import subprocess
import sys

import profiles as profiles_mod
import screener as screener_mod

SCREENER_RESULTS = Path(__file__).parent / 'results'
MIN_RUN_INTERVAL_SEC = 300   # don't let a button masher rate-limit our IP

LOOPBACK = {'127.0.0.1', '::1', 'localhost'}
# Headers a reverse proxy adds when it forwards someone else's request.
PROXY_HEADERS = ('X-Forwarded-For', 'X-Real-IP', 'Forwarded', 'X-Forwarded-Host')
# Shared secret for anything not coming from the machine itself. The screener
# page prompts for it and replays it as X-Admin-Token. Deliberately thin: it
# stops a passer-by, not someone who reads the JS and calls the API directly.
# Leave it empty to allow loopback only.
ADMIN_TOKEN = os.environ.get('SCREENER_ADMIN_TOKEN', '').strip()


def is_local_request():
    """True only for a request that really originated on this machine.

    remote_addr alone is NOT enough: put nginx in front and every visitor
    arrives as 127.0.0.1, so a naive loopback check would wave the whole
    internet through. A forwarded request always carries a proxy header, so
    the presence of one disqualifies it regardless of remote_addr.
    """
    if any(request.headers.get(h) for h in PROXY_HEADERS):
        return False
    return (request.remote_addr or '') in LOOPBACK


def admin_ok():
    if is_local_request():
        return True
    if ADMIN_TOKEN:
        sent = request.headers.get('X-Admin-Token', '')
        # constant-time compare so the token cannot be guessed byte by byte
        return hmac.compare_digest(sent, ADMIN_TOKEN)
    return False


def admin_required(fn):
    @wraps(fn)
    def guard(*a, **kw):
        if not admin_ok():
            return jsonify({
                "error": "Perlu password.",
                "locked": True,
                "hint": ("Set SCREENER_ADMIN_TOKEN di .env kalau belum."
                         if not ADMIN_TOKEN else "Password salah atau belum diisi."),
            }), 403
        return fn(*a, **kw)
    return guard


def _screener_dates():
    if not SCREENER_RESULTS.exists():
        return []
    return sorted((f.stem for f in SCREENER_RESULTS.glob('*.json')
                   if f.stem != 'status'), reverse=True)


@app.route('/screener')
def screener_page():
    return render_template('screener.html')


@app.route('/api/screener')
@admin_required
def screener_data():
    dates = _screener_dates()
    if not dates:
        return jsonify({"error": "Belum ada hasil screener. Klik 'Jalankan' "
                                 "atau: python3 screener.py"})

    requested = (request.args.get('date') or '').strip()
    date = requested if requested in dates else dates[0]
    try:
        payload = json.loads((SCREENER_RESULTS / f"{date}.json").read_text())
    except Exception as e:
        print(f"Screener read error: {e}")
        return jsonify({"error": f"Gagal membaca hasil {date}."})

    payload['available_dates'] = dates
    return jsonify(payload)


@app.route('/api/screener/status')
def screener_status():
    st = screener_mod.read_status() or {"state": "idle"}
    st['admin'] = admin_ok()
    st['needs_password'] = bool(ADMIN_TOKEN) and not st['admin']
    return jsonify(st)


@app.route('/api/screener/profiles', methods=['GET'])
@admin_required
def screener_profiles():
    try:
        return jsonify({"profiles": profiles_mod.load(),
                        "builtin": profiles_mod.BUILTIN})
    except Exception as e:
        print(f"Profiles read error: {e}")
        return jsonify({"error": str(e)})


@app.route('/api/screener/profiles', methods=['POST'])
@admin_required
def screener_profiles_save():
    patch = request.get_json(silent=True)
    if not isinstance(patch, dict):
        return jsonify({"error": "Body harus objek JSON."}), 400
    try:
        # save_overrides validates the MERGED result, so a partial patch that
        # would produce an invalid profile is rejected before it is written.
        return jsonify({"profiles": profiles_mod.save_overrides(patch)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Profiles save error: {e}")
        return jsonify({"error": "Gagal menyimpan setelan."}), 500


@app.route('/api/screener/run', methods=['POST'])
@admin_required
def screener_run():
    if screener_mod.run_in_progress():
        return jsonify({"error": "Run lain sedang berjalan.",
                        "status": screener_mod.read_status()}), 409

    last = screener_mod.read_status() or {}
    if last.get('state') == 'done' and last.get('updated'):
        try:
            age = datetime.now(screener_mod.WIB) - datetime.fromisoformat(last['updated'])
            if age.total_seconds() < MIN_RUN_INTERVAL_SEC:
                wait = int(MIN_RUN_INTERVAL_SEC - age.total_seconds())
                return jsonify({"error": f"Baru saja jalan. Tunggu {wait} detik."}), 429
        except (ValueError, TypeError):
            pass

    body = request.get_json(silent=True) or {}
    # --force because the lock check above already ran. Without it the child
    # would boot, read the 'running' status we are about to write, mistake its
    # own parent's marker for a rival run, and exit immediately.
    cmd = [sys.executable, str(Path(__file__).parent / 'screener.py'), '--force']
    for name in (body.get('profiles') or []):
        if name in profiles_mod.load():
            cmd += ['--profile', name]
    if body.get('dry_run'):
        cmd.append('--dry-run')

    try:
        SCREENER_RESULTS.mkdir(exist_ok=True)
        logfile = open(SCREENER_RESULTS / 'run.log', 'ab')
        subprocess.Popen(cmd, cwd=str(Path(__file__).parent),
                         stdout=logfile, stderr=subprocess.STDOUT,
                         start_new_session=True)   # survives a gunicorn reload
    except Exception as e:
        print(f"Screener spawn error: {e}")
        return jsonify({"error": f"Gagal menjalankan: {e}"}), 500

    screener_mod.write_status(state='running', stage='starting',
                              started=datetime.now(screener_mod.WIB).isoformat())
    return jsonify({"started": True})


@app.route('/api/ai-insights', methods=['POST'])
def ai_insights():
    try:
        body = request.get_json(silent=True)
        if not body:
            return jsonify({"insights": {}, "error": "empty body"})
        ticker = body.get('ticker', '')
        data = body.get('data', {}) or {}
        insights, raw_or_err = get_all_insights(ticker, data)
        if not insights:
            print(f"AI insights failed or empty: {raw_or_err}")
        return jsonify({"insights": insights, "raw": raw_or_err})
    except Exception as e:
        print(f"AI Route Error: {e}")
        return jsonify({"insights": {}, "error": str(e)})


@app.route('/api/ai-test')
def ai_test():
    import os, requests as req, time, jwt as pyjwt

    api_key = os.environ.get('GLM_API_KEY', '')
    model = os.environ.get('GLM_MODEL', 'GLM-4.5-Flash')
    url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
    payload = {"model": model, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 50}

    results = {}

    # test A: raw key as Bearer
    try:
        r = req.post(url, json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, timeout=15)
        results['raw_key'] = {"status": r.status_code, "body": r.json()}
    except Exception as e:
        results['raw_key'] = {"error": str(e)}

    # test B: JWT token
    try:
        key_id, secret = api_key.split('.', 1)
        now_ms = int(time.time() * 1000)
        token = pyjwt.encode({"api_key": key_id, "exp": now_ms + 60000, "timestamp": now_ms},
                              secret, algorithm="HS256", headers={"alg": "HS256", "sign_type": "SIGN"})
        r2 = req.post(url, json=payload, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, timeout=15)
        results['jwt'] = {"status": r2.status_code, "body": r2.json()}
    except Exception as e:
        results['jwt'] = {"error": str(e)}

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
