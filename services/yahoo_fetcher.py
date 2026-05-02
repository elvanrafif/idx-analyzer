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
    hist_6m = stock.history(period='6mo')
    hist_1y = stock.history(period='1y')
    hist_3m = stock.history(period='3mo')
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
                except:
                    row[cols[j]] = None
            data[str(idx)] = row
        return {"columns": cols, "data": data}
    except:
        return None
