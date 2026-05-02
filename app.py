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

load_dotenv()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze')
def analyze():
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({"error": "Ticker tidak boleh kosong."})

    try:
        data = fetch_ticker_data(ticker)
        if data is None:
            return jsonify({"error": f"Data emiten {ticker} tidak ditemukan di IHSG."})

        info = data['info']
        bs = data['balance_sheet']
        fs = data['financials']
        cf = data['cashflow']

        sharpe = calculate_sharpe(data['hist_1y'])
        sortino = calculate_sortino(data['hist_1y'])
        piotroski = calculate_piotroski(bs, fs, cf)
        altman = calculate_altman_z(bs, fs)
        macd_bb = calculate_macd_bb(data['hist_6m'])
        rsi = calculate_rsi(data['hist_3m'])
        sma = calculate_sma(data['hist_1y'])
        rvol = calculate_rvol(data['hist_3m'])
        fcf_yield = calculate_fcf_yield(info)
        composite = calculate_composite(
            info, piotroski, altman, macd_bb, rsi,
            sharpe, sortino, rvol, data['hist_1y']
        )

        return jsonify({
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
            "fcf_yield": fcf_yield,
            "sharpe": sharpe,
            "sortino": sortino,
            "composite": composite,
        })
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": f"Error teknis: {str(e)}"})


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
