import os
import re
from openai import OpenAI

SECTIONS = ['valuasi', 'technical', 'scoring', 'composite', 'consensus']


def get_client():
    return OpenAI(
        api_key=os.environ.get('GLM_API_KEY', ''),
        base_url=os.environ.get('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4'),
    )


def get_model():
    return os.environ.get('GLM_MODEL', 'GLM-4.5-Flash')


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

    prompt = f"""Kamu adalah analis saham IDX. Analisis saham {ticker} berdasarkan data berikut dan berikan insight untuk 5 area.

DATA:
- Valuasi: P/E={_safe(i.get('trailingPE'))}, P/BV={_safe(i.get('priceToBook'))}, PEG={_safe(i.get('pegRatio'))}, P/S={_safe(i.get('priceToSalesTrailing12Months'))}
- Teknikal: MACD={_safe(macd.get('signal_label'))}, RSI={_safe(rsi.get('value'))} ({_safe(rsi.get('signal'))}), BB={_safe(bb.get('signal'))} (%B={bb_pct_str}), SMA50={_safe(sma.get('sma50'))}, Golden Cross={_safe(sma.get('golden_cross'))}
- Scoring: Piotroski={_safe(piotroski.get('score'))}/9 ({_safe(piotroski.get('rating'))}), Altman Z={_safe(altman.get('z_score'))} ({_safe(altman.get('zone'))})
- Composite: Score={_safe(comp.get('final'))}/100, Signal={_safe(comp.get('signal'))}, Fundamental={_safe(comp_components.get('Fundamental'))}, Technical={_safe(comp_components.get('Technical'))}, Risk={_safe(comp_components.get('Risk'))}, Momentum={_safe(comp_components.get('Momentum'))}
- Consensus: Signal={_safe(comp.get('signal'))}

FORMAT RESPONS (ikuti PERSIS, jangan tambah teks lain di luar format ini):
[VALUASI]
<2-3 kalimat insight valuasi>
[TECHNICAL]
<2-3 kalimat insight teknikal>
[SCORING]
<2-3 kalimat insight scoring>
[COMPOSITE]
<2-3 kalimat kesimpulan composite>
[CONSENSUS]
<2-3 kalimat rangkuman consensus>

Gunakan Bahasa Indonesia. Jangan gunakan markdown."""

    return prompt


def parse_combined_response(text):
    results = {}
    pattern = r'\[(' + '|'.join(s.upper() for s in SECTIONS) + r')\]\s*(.*?)(?=\[(?:' + '|'.join(s.upper() for s in SECTIONS) + r')\]|$)'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    for label, content in matches:
        key = label.lower()
        results[key] = content.strip()
    return results


def get_all_insights(ticker, data):
    prompt = build_combined_prompt(ticker, data)
    try:
        client = get_client()
        model = get_model()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Kamu adalah analis saham IDX yang ahli. Ikuti format respons yang diminta dengan tepat."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.7,
            timeout=45.0,
        )
        raw = response.choices[0].message.content.strip()
        print(f"GLM RAW RESPONSE:\n{raw}\n---END---")
        insights = parse_combined_response(raw)
        if not insights:
            print(f"AI parse failed, raw response: {raw[:500]}")
        return insights, raw  # temporarily return raw for debugging
    except Exception as e:
        err = f"AI Error (all) model={get_model()}: {e}"
        print(err)
        return {}, str(e)


def test_connection():
    try:
        client = get_client()
        model = get_model()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
            timeout=15.0,
        )
        return True, response.choices[0].message.content.strip()
    except Exception as e:
        return False, str(e)
