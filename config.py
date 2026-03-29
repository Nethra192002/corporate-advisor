# config.py
from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

COMPANIES = {
    "AAPL": "Apple Inc.",
    "TSLA": "Tesla Inc.",
    "NVDA": "Nvidia Corporation",
    "SPOT": "Spotify Technology",
    "MSFT": "Microsoft Corporation",
}

# Financial model assumptions
MODEL_ASSUMPTIONS = {
    "base_growth_premium":   0.00,   # historical avg
    "upside_growth_premium": 0.05,   # +5% on top of historical
    "downside_growth_cut":   0.50,   # half of historical
    "projection_years":      5,
    "funding_amount_m":      500,    # $500M default simulation
}