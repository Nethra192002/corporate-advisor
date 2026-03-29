# test_ingestion.py  (run this: python test_ingestion.py)
from ingestion.fetch import fetch_financials
from ingestion.wiki  import fetch_company_context

if __name__ == "__main__":
    ticker = "AAPL"

    fin  = fetch_financials(ticker)
    wiki = fetch_company_context(ticker)

    print("\n--- FINANCIALS ---")
    print(f"Sector:     {fin.get('sector')}")
    print(f"Market cap: ${fin.get('market_cap', 0):,.0f}")
    print(f"Revenue:    {fin.get('revenue')}")
    print(f"Net income: {fin.get('net_income')}")
    print(f"Cash:       ${fin.get('cash', 0):,.0f}")
    print(f"Debt:       ${fin.get('total_debt', 0):,.0f}")

    print("\n--- COMPANY CONTEXT ---")
    print(f"Description: {wiki.get('description')}")
    print(f"Wiki URL:    {wiki.get('wiki_url')}")
