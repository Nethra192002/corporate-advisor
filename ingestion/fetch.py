# ingestion/fetch.py
import yfinance as yf


def fetch_financials(ticker: str) -> dict:
    """
    Pull real financial data from Yahoo Finance via yfinance.
    Returns a clean dict with everything the pipeline needs.
    """
    print(f"[Ingestion] Fetching financials for {ticker}...")

    try:
        stock = yf.Ticker(ticker)

        info        = stock.info
        income      = stock.financials          # annual, most recent first
        balance     = stock.balance_sheet
        cashflow    = stock.cashflow

        # --- Revenue (last 4 years, oldest → newest) ---
        if "Total Revenue" in income.index:
            revenue_series = income.loc["Total Revenue"].dropna().sort_index()
            revenue = [float(v) for v in revenue_series.values]
            revenue_dates = [str(d.year) for d in revenue_series.index]
        else:
            revenue, revenue_dates = [], []

        # --- Net income ---
        if "Net Income" in income.index:
            net_income_series = income.loc["Net Income"].dropna().sort_index()
            net_income = [float(v) for v in net_income_series.values]
        else:
            net_income = []

        # --- Free cash flow ---
        if "Free Cash Flow" in cashflow.index:
            fcf_series = cashflow.loc["Free Cash Flow"].dropna().sort_index()
            free_cash_flow = [float(v) for v in fcf_series.values]
        else:
            free_cash_flow = []

        # --- Balance sheet items ---
        def get_balance(label):
            if label in balance.index:
                val = balance.loc[label].dropna()
                return float(val.iloc[0]) if len(val) > 0 else None
            return None

        total_debt       = get_balance("Total Debt")
        cash             = get_balance("Cash And Cash Equivalents")
        total_assets     = get_balance("Total Assets")
        total_equity     = get_balance("Stockholders Equity")

        # --- Key stats from info ---
        market_cap    = info.get("marketCap")
        sector        = info.get("sector", "Unknown")
        industry      = info.get("industry", "Unknown")
        employees     = info.get("fullTimeEmployees")
        country       = info.get("country", "Unknown")
        website       = info.get("website", "")
        pe_ratio      = info.get("trailingPE")
        beta          = info.get("beta")
        dividend_rate = info.get("dividendRate")

        result = {
            "ticker":         ticker,
            "sector":         sector,
            "industry":       industry,
            "employees":      employees,
            "country":        country,
            "website":        website,
            "market_cap":     market_cap,
            "pe_ratio":       pe_ratio,
            "beta":           beta,
            "dividend_rate":  dividend_rate,
            "revenue":        revenue,
            "revenue_dates":  revenue_dates,
            "net_income":     net_income,
            "free_cash_flow": free_cash_flow,
            "total_debt":     total_debt,
            "cash":           cash,
            "total_assets":   total_assets,
            "total_equity":   total_equity,
        }

        print(f"[Ingestion] ✓ {ticker} — revenue records: {len(revenue)}, "
              f"market cap: ${market_cap:,.0f}" if market_cap else
              f"[Ingestion] ✓ {ticker} fetched (market cap unavailable)")

        return result

    except Exception as e:
        print(f"[Ingestion] ✗ Failed to fetch {ticker}: {e}")
        return {"ticker": ticker, "error": str(e)}