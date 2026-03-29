# ingestion/wiki.py
import requests

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

WIKI_TITLES = {
    "AAPL": "Apple_Inc.",
    "TSLA": "Tesla,_Inc.",
    "NVDA": "Nvidia",
    "SPOT": "Spotify",
    "MSFT": "Microsoft",
}


def fetch_company_context(ticker: str) -> dict:
    print(f"[Wiki] Fetching context for {ticker}...")

    title = WIKI_TITLES.get(ticker)
    if not title:
        print(f"[Wiki] No Wikipedia title configured for {ticker}")
        return {"description": "", "wiki_url": ""}

    try:
        response = requests.get(
            f"{WIKI_API}{title}",
            headers={"User-Agent": "CorporateAdvisor/1.0 (hackathon project)"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        description = data.get("extract", "")
        wiki_url    = data.get("content_urls", {}).get("desktop", {}).get("page", "")

        # Trim to first 3 sentences
        sentences   = description.split(". ")
        short_desc  = ". ".join(sentences[:3]) + ("." if len(sentences) > 3 else "")

        print(f"[Wiki] ✓ {ticker} — {len(short_desc)} chars fetched")

        return {
            "description": short_desc,
            "full_description": description,
            "wiki_url": wiki_url,
        }

    except Exception as e:
        print(f"[Wiki] ✗ Failed for {ticker}: {e}")
        return {"description": "", "wiki_url": ""}