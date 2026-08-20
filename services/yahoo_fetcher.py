import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone


def fetch_ticker_data(ticker):
    stock = yf.Ticker(f"{ticker}.JK")
    info = stock.info
    if not info or not (info.get('regularMarketPrice') or info.get('currentPrice')):
        return None
    clean_info = {
        k: (None if isinstance(v, float) and pd.isna(v) else v)
        for k, v in info.items()
    }
    # One 2y pull, sliced locally: ADX/EMA200 need the long warm-up, and
    # three separate history() calls were three round-trips for the same bars.
    hist_2y = stock.history(period='2y')
    hist_1y = hist_2y.tail(252)
    hist_6m = hist_2y.tail(126)
    hist_3m = hist_2y.tail(63)
    balance_sheet = stock.balance_sheet
    financials = stock.financials
    cashflow = stock.cashflow
    quarterly = stock.quarterly_financials
    return {
        'ticker': ticker,
        'info': clean_info,
        'hist_6m': hist_6m,
        'hist_1y': hist_1y,
        'hist_3m': hist_3m,
        'hist_2y': hist_2y,
        'balance_sheet': balance_sheet,
        'financials': financials,
        'cashflow': cashflow,
        'quarterly': quarterly,
        'updated': datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M WIB"),
    }


def df_to_dict(df):
    if df is None or df.empty:
        return None
    try:
        cols = [
            f"Q{c.quarter} {c.year}" if hasattr(c, 'quarter') else str(c.year)
            for c in df.columns[:4]
        ]
        data = {}
        for idx in df.index:
            row = {}
            for j, col in enumerate(df.columns[:4]):
                try:
                    v = df.loc[idx, col]
                    row[cols[j]] = None if pd.isna(v) else float(v)
                except Exception:
                    row[cols[j]] = None
            data[str(idx)] = row
        return {"columns": cols, "data": data}
    except Exception as e:
        print(f"df_to_dict error: {e}")
        return None
