import os
from openai import OpenAI


def get_client():
    return OpenAI(
        api_key=os.environ.get('GLM_API_KEY', ''),
        base_url=os.environ.get('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4'),
    )


def get_model():
    return os.environ.get('GLM_MODEL', 'GLM-4.5-Flash')


SECTION_PROMPTS = {
    'valuasi': (
        "Analisa valuasi saham {ticker} berdasarkan data berikut: "
        "P/E {pe}, P/BV {pb}, PEG {peg}, Price to Sales {ps}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown. Langsung tulis insight saja."
    ),
    'profitabilitas': (
        "Analisa profitabilitas saham {ticker}: "
        "ROE {roe}, ROA {roa}, Net Margin {npm}, Operating Margin {opm}, "
        "Revenue Growth {rg}, Earnings Growth {eg}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'kesehatan': (
        "Analisa kesehatan keuangan saham {ticker}: "
        "Current Ratio {cr}, Quick Ratio {qr}, Debt to Equity {de}, "
        "Total Debt {td}, Total Cash {tc}, Free Cash Flow {fcf}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'dividen': (
        "Analisa dividen saham {ticker}: "
        "Dividend Yield {dy}, Dividend Rate {dr}, Payout Ratio {pr}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'technical': (
        "Analisa sinyal teknikal saham {ticker}: "
        "MACD {macd_signal}, RSI {rsi_val} ({rsi_signal}), "
        "Bollinger Bands {bb_signal} (%B {bb_pct}), Bandwidth {bb_bw}, "
        "SMA50 {sma50}, Golden Cross {gc}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'scoring': (
        "Interpretasi scoring saham {ticker}: "
        "Piotroski F-Score {fscore}/9 ({frating}), Altman Z-Score {zscore} ({zzone}). "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'composite': (
        "Beri kesimpulan akhir untuk saham {ticker} berdasarkan "
        "composite score {score}/100 dengan sinyal {signal}. "
        "Komponen: Fundamental {fund}, Technical {tech}, Risk {risk}, Momentum {mom}, Sentiment {sent}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'consensus': (
        "Rangkum consensus teknikal saham {ticker}: "
        "{buy_count} indikator bullish, {neut_count} netral, {sell_count} bearish. "
        "Verdict: {verdict}. Detail: {details}. "
        "Berikan insight singkat 2-3 kalimat yang to the point dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
    'financial': (
        "Tren keuangan saham {ticker} berdasarkan laporan tahunan terakhir. "
        "Data: {summary}. "
        "Berikan insight singkat 2-3 kalimat tentang tren yang terlihat dalam Bahasa Indonesia. "
        "Jangan gunakan format markdown."
    ),
}


def build_prompt(section, ticker, data):
    template = SECTION_PROMPTS.get(section, '')
    if not template:
        return None
    try:
        merged = {'ticker': ticker}
        if isinstance(data, dict):
            for k, v in data.items():
                merged[k] = v if v is not None else 'N/A'
        import re
        placeholders = set(re.findall(r'\{(\w+)\}', template))
        safe = {k: str(merged.get(k, 'N/A')) for k in placeholders}
        return template.format(**safe)
    except Exception as e:
        print(f"Prompt build error ({section}): {e}")
        return None


def get_ai_insight(section, ticker, data):
    prompt = build_prompt(section, ticker, data)
    if not prompt:
        return None, "No prompt template for section: " + section
    try:
        client = get_client()
        model = get_model()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Kamu adalah analis saham IDX yang ahli. Berikan analisis singkat, tajam, dan to the point."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.7,
            timeout=30.0,
        )
        return response.choices[0].message.content.strip(), None
    except Exception as e:
        err = f"AI Error ({section}) model={get_model()}: {e}"
        print(err)
        return None, str(e)


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
