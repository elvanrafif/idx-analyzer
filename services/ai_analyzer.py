import os
import re
import time
import jwt
from openai import OpenAI

SECTIONS = ['key_metrics', 'valuasi', 'technical', 'piotroski', 'altman', 'composite', 'consensus', 'key_levels']

SYSTEM_PROMPT = "Kamu adalah asisten yang menjelaskan data keuangan secara edukatif."


# ── GLM (ZhipuAI) ────────────────────────────────────────────────────────────

def _generate_glm_token(api_key: str) -> str:
    try:
        key_id, secret = api_key.split('.', 1)
    except ValueError:
        return api_key
    now_ms = int(time.time() * 1000)
    return jwt.encode(
        {"api_key": key_id, "exp": now_ms + 600_000, "timestamp": now_ms},
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )


def _glm_client():
    token = _generate_glm_token(os.environ.get('GLM_API_KEY', ''))
    return OpenAI(
        api_key=token,
        base_url=os.environ.get('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4'),
    )


def _glm_model():
    return os.environ.get('GLM_MODEL', 'GLM-4.5-Flash')


# ── Google Gemini ─────────────────────────────────────────────────────────────

def _google_client():
    return OpenAI(
        api_key=os.environ.get('GOOGLE_API_KEY', ''),
        base_url='https://generativelanguage.googleapis.com/v1beta/openai/',
    )


def _google_model():
    return os.environ.get('GOOGLE_MODEL', 'gemini-2.0-flash')


# ── Shared ────────────────────────────────────────────────────────────────────

def _safe(val):
    return str(val) if val is not None else 'N/A'


def _call(client, model, prompt, max_tokens, timeout, label):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
        timeout=timeout,
    )
    content = response.choices[0].message.content
    finish = response.choices[0].finish_reason
    print(f"{label} finish={finish}, content_len={len(content) if content else 0}")
    return content or ''


def build_combined_prompt(ticker, data):
    d = data
    i = d.get('info', {}) or {}
    comp = d.get('composite', {}) or {}
    comp_components = comp.get('components', {}) or {}
    piotroski = d.get('piotroski', {}) or {}
    altman = d.get('altman', {}) or {}
    macd_bb = d.get('macd_bb', {}) or {}
    macd = macd_bb.get('macd', {}) or {}
    bb = macd_bb.get('bb', {}) or {}
    rsi = d.get('rsi', {}) or {}
    sma = d.get('sma', {}) or {}
    kl = d.get('key_levels', {}) or {}

    bb_pct = bb.get('pct_b')
    bb_pct_str = f"{float(bb_pct)*100:.0f}" if bb_pct is not None else 'N/A'
    price = i.get('regularMarketPrice') or i.get('currentPrice')
    wk52h = i.get('fiftyTwoWeekHigh')
    wk52l = i.get('fiftyTwoWeekLow')
    wk52pos = f"{(price - wk52l) / (wk52h - wk52l) * 100:.0f}%" if price and wk52h and wk52l and wk52h != wk52l else 'N/A'

    return f"""Tolong jelaskan data keuangan emiten {ticker} berdasarkan angka-angka berikut. \
Ini untuk keperluan edukasi dan pemahaman laporan keuangan, bukan rekomendasi investasi.

Data emiten:
- Harga: Rp{_safe(price)}, Posisi 52 minggu={wk52pos}, Market Cap={_safe(i.get('marketCap'))}
- Rasio harga: P/E={_safe(i.get('trailingPE'))}, P/BV={_safe(i.get('priceToBook'))}, PEG={_safe(i.get('pegRatio'))}, P/S={_safe(i.get('priceToSalesTrailing12Months'))}
- Profitabilitas: ROE={_safe(i.get('returnOnEquity'))}, ROA={_safe(i.get('returnOnAssets'))}, Net Margin={_safe(i.get('profitMargins'))}
- Indikator teknikal: MACD={_safe(macd.get('signal_label'))}, RSI={_safe(rsi.get('value'))} ({_safe(rsi.get('signal'))}), Bollinger={_safe(bb.get('signal'))} (%B={bb_pct_str}), SMA50={_safe(sma.get('sma50'))}, Golden Cross={_safe(sma.get('golden_cross'))}
- Piotroski F-Score: {_safe(piotroski.get('score'))}/9, Rating={_safe(piotroski.get('rating'))}
- Altman Z-Score: {_safe(altman.get('z_score'))}, Zone={_safe(altman.get('zone'))}, Deskripsi={_safe(altman.get('desc'))}
- Skor komposit: {_safe(comp.get('final'))}/100, Sinyal={_safe(comp.get('signal'))}, Fundamental={_safe(comp_components.get('Fundamental'))}, Teknikal={_safe(comp_components.get('Technical'))}, Risiko={_safe(comp_components.get('Risk'))}, Momentum={_safe(comp_components.get('Momentum'))}

Jelaskan masing-masing bagian berikut dalam Bahasa Indonesia, 2-3 kalimat tiap bagian. \
Gunakan format persis seperti ini (jangan ada teks di luar format):

[KEY_METRICS]
ringkasan singkat kondisi emiten secara keseluruhan berdasarkan harga dan valuasi
[VALUASI]
penjelasan rasio harga P/E, P/BV, PEG
[TECHNICAL]
penjelasan sinyal MACD, RSI, Bollinger Bands, dan Moving Average
[PIOTROSKI]
penjelasan khusus Piotroski F-Score dan artinya
[ALTMAN]
penjelasan khusus Altman Z-Score dan artinya
[COMPOSITE]
penjelasan skor komposit dan sinyal keseluruhan
[CONSENSUS]
ringkasan akhir dari semua indikator
[KEY_LEVELS]
penjelasan posisi harga terhadap level support dan resistance kunci (S1={_safe(kl.get('s1'))}, S2={_safe(kl.get('s2'))}, R1={_safe(kl.get('r1'))}, R2={_safe(kl.get('r2'))})"""


def parse_combined_response(text):
    results = {}
    keys = [s.upper().replace('_', r'[_\s]?') for s in SECTIONS]
    pattern = r'\[(' + '|'.join(keys) + r')\]\s*(.*?)(?=\[(?:' + '|'.join(keys) + r')\]|$)'
    for label, content in re.findall(pattern, text, re.DOTALL | re.IGNORECASE):
        key = re.sub(r'[\s_]+', '_', label.strip()).lower()
        results[key] = content.strip()
    return results


def get_all_insights(ticker, data):
    prompt = build_combined_prompt(ticker, data)
    errors = []

    # 1. Try GLM
    if os.environ.get('GLM_API_KEY'):
        try:
            raw = _call(_glm_client(), _glm_model(), prompt, max_tokens=4000, timeout=60.0, label='GLM')
            if raw:
                insights = parse_combined_response(raw)
                if insights:
                    return insights, raw
                errors.append(f"GLM parse failed: {raw[:100]}")
            else:
                errors.append("GLM empty content")
        except Exception as e:
            errors.append(f"GLM error: {e}")
            print(f"GLM failed, trying Google fallback: {e}")

    # 2. Fallback: Google Gemini
    if os.environ.get('GOOGLE_API_KEY'):
        try:
            raw = _call(_google_client(), _google_model(), prompt, max_tokens=1500, timeout=30.0, label='Google')
            if raw:
                insights = parse_combined_response(raw)
                if insights:
                    return insights, raw
                errors.append(f"Google parse failed: {raw[:100]}")
            else:
                errors.append("Google empty content")
        except Exception as e:
            errors.append(f"Google error: {e}")
            print(f"Google fallback failed: {e}")

    return {}, ' | '.join(errors) or 'no providers configured'


def test_connection():
    results = {}

    if os.environ.get('GLM_API_KEY'):
        try:
            r = _call(_glm_client(), _glm_model(), "Say OK in one word.", max_tokens=500, timeout=15.0, label='GLM-test')
            results['glm'] = {'ok': bool(r), 'response': r[:100], 'model': _glm_model()}
        except Exception as e:
            results['glm'] = {'ok': False, 'error': str(e), 'model': _glm_model()}

    if os.environ.get('GOOGLE_API_KEY'):
        try:
            r = _call(_google_client(), _google_model(), "Say OK in one word.", max_tokens=50, timeout=15.0, label='Google-test')
            results['google'] = {'ok': bool(r), 'response': r[:100], 'model': _google_model()}
        except Exception as e:
            results['google'] = {'ok': False, 'error': str(e), 'model': _google_model()}

    if not results:
        return False, 'no API keys configured (GLM_API_KEY or GOOGLE_API_KEY)'
    return True, results
