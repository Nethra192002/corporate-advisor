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
    "base_growth_premium":   0.00,   
    "upside_growth_premium": 0.05,   
    "downside_growth_cut":   0.50,   
    "projection_years":      5,
    "funding_amount_m":      500,    
}