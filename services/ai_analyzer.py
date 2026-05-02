import os
import re
import time
import jwt
from openai import OpenAI

SECTIONS = ['valuasi', 'technical', 'scoring', 'composite', 'consensus']


def _generate_token(api_key: str) -> str:
    """Generate ZhipuAI JWT from {id}.{secret} key format."""
    try:
        key_id, secret = api_key.split('.', 1)
    except ValueError:
        return api_key  # not the {id}.{secret} format, use as-is
    now_ms = int(time.time() * 1000)
    payload = {
        "api_key": key_id,
        "exp": now_ms + 600_000,  # 10 minutes
        "timestamp": now_ms,
    }
    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )


def get_client():
    raw_key = os.environ.get('GLM_API_KEY', '')
    token = _generate_token(raw_key)
    return OpenAI(
        api_key=token,
        base_url=os.environ.get('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4'),
    )


def get_model():
    return os.environ.get('GLM_MODEL', 'GLM-4.6')


def _safe(val):
    return str(val) if val is not None else 'N/A'


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

    bb_pct = bb.get('pct_b')
    bb_pct_str = f"{float(bb_pct)*100:.0f}" if bb_pct is not None else 'N/A'

    return f"""Tolong jelaskan data keuangan emiten {ticker} berdasarkan angka-angka berikut. \
Ini untuk keperluan edukasi dan pemahaman laporan keuangan, bukan rekomendasi investasi.

Data emiten:
- Rasio harga: P/E={_safe(i.get('trailingPE'))}, P/BV={_safe(i.get('priceToBook'))}, PEG={_safe(i.get('pegRatio'))}, P/S={_safe(i.get('priceToSalesTrailing12Months'))}
- Indikator teknikal: MACD={_safe(macd.get('signal_label'))}, RSI={_safe(rsi.get('value'))} ({_safe(rsi.get('signal'))}), Bollinger={_safe(bb.get('signal'))} (%B={bb_pct_str}), SMA50={_safe(sma.get('sma50'))}, Golden Cross={_safe(sma.get('golden_cross'))}
- Skor fundamental: Piotroski={_safe(piotroski.get('score'))}/9 ({_safe(piotroski.get('rating'))}), Altman Z={_safe(altman.get('z_score'))} ({_safe(altman.get('zone'))})
- Skor komposit: {_safe(comp.get('final'))}/100, Sinyal={_safe(comp.get('signal'))}, Fundamental={_safe(comp_components.get('Fundamental'))}, Teknikal={_safe(comp_components.get('Technical'))}, Risiko={_safe(comp_components.get('Risk'))}, Momentum={_safe(comp_components.get('Momentum'))}

Jelaskan masing-masing bagian berikut dalam Bahasa Indonesia, 2-3 kalimat tiap bagian. \
Gunakan format persis seperti ini:

[VALUASI]
penjelasan rasio harga di sini
[TECHNICAL]
penjelasan indikator teknikal di sini
[SCORING]
penjelasan skor fundamental di sini
[COMPOSITE]
penjelasan skor komposit di sini
[CONSENSUS]
ringkasan keseluruhan di sini"""


def parse_combined_response(text):
    results = {}
    pattern = r'\[(' + '|'.join(s.upper() for s in SECTIONS) + r')\]\s*(.*?)(?=\[(?:' + '|'.join(s.upper() for s in SECTIONS) + r')\]|$)'
    for label, content in re.findall(pattern, text, re.DOTALL | re.IGNORECASE):
        results[label.lower()] = content.strip()
    return results


def get_all_insights(ticker, data):
    prompt = build_combined_prompt(ticker, data)
    try:
        client = get_client()
        model = get_model()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Kamu adalah asisten yang menjelaskan data keuangan secara edukatif."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.7,
            timeout=30.0,
        )
        content = response.choices[0].message.content
        finish = response.choices[0].finish_reason
        print(f"GLM finish={finish}, content_len={len(content) if content else 0}")
        if not content:
            return {}, f"empty_content|finish={finish}"
        raw = content.strip()
        insights = parse_combined_response(raw)
        if not insights:
            print(f"Parse failed, raw: {raw[:300]}")
        return insights, raw
    except Exception as e:
        err = f"AI Error model={get_model()}: {e}"
        print(err)
        return {}, str(e)


def test_connection():
    try:
        client = get_client()
        model = get_model()
        r1 = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=500,
            timeout=15.0,
        )
        basic = r1.choices[0].message.content or ""
        finish1 = r1.choices[0].finish_reason

        r2 = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "What does P/E ratio mean? One sentence."}],
            max_tokens=500,
            timeout=15.0,
        )
        financial = r2.choices[0].message.content or ""
        finish2 = r2.choices[0].finish_reason

        return True, {
            "basic": basic, "finish1": finish1,
            "financial": financial, "finish2": finish2,
            "model": model,
        }
    except Exception as e:
        return False, str(e)
