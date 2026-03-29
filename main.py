# main.py
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import COMPANIES
from ingestion.fetch import fetch_financials
from ingestion.wiki import fetch_company_context
from processing.profile import build_profile
from modeling.model import build_model
from simulation.simulator import simulate_funding
from agent.advisor import run_advisor
from rag.indexer import build_index
from rag.retriever import query_index
from processing.anomaly import score_anomaly

app = FastAPI(title="Corporate Finance Autopilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache — one entry per ticker
cache: dict = {}


# ── Models ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    ticker: str
    question: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/companies")
def get_companies():
    """Return the preset company list for the frontend picker."""
    return {"companies": [
        {"ticker": k, "name": v} for k, v in COMPANIES.items()
    ]}


@app.post("/analyse/{ticker}")
async def analyse(ticker: str):
    """
    Run the full pipeline for a ticker.
    Stores result in cache. Returns summary + full result.
    """
    ticker = ticker.upper()
    if ticker not in COMPANIES:
        raise HTTPException(status_code=404, detail=f"{ticker} not in preset list")

    print(f"\n{'='*50}")
    print(f"  PIPELINE START — {ticker}")
    print(f"{'='*50}")

    try:
        # ① Ingestion
        financials = fetch_financials(ticker)
        if "error" in financials:
            raise HTTPException(status_code=502, detail=f"Data fetch failed: {financials['error']}")
        wiki = fetch_company_context(ticker)

        # ② Processing
        profile = build_profile(financials, wiki)

        profile["anomaly"] = score_anomaly(profile, cache)

        # ③ Modeling
        model = build_model(profile)

        # ④ Simulation
        simulation = simulate_funding(profile, model)

        # ⑤ AI Advisor
        advice = await run_advisor(profile, model, simulation)

        # ⑥ RAG index
        index_data = build_index(profile, model, simulation, advice)

        # Store in cache
        result = {
            "ticker":     ticker,
            "name":       COMPANIES[ticker],
            "profile":    profile,
            "model":      model,
            "simulation": simulation,
            "advice":     advice,
            "index":      index_data,
        }
        cache[ticker] = result

        print(f"\n{'='*50}")
        print(f"  PIPELINE COMPLETE — {ticker}")
        print(f"{'='*50}\n")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Pipeline] ✗ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/{ticker}")
def get_results(ticker: str):
    """Return cached results without re-running the pipeline."""
    ticker = ticker.upper()
    if ticker not in cache:
        raise HTTPException(status_code=404, detail="No results yet — run /analyse first")
    return cache[ticker]


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    RAG-powered chat — retrieves relevant context then asks Groq.
    """
    ticker = req.ticker.upper()
    if ticker not in cache:
        raise HTTPException(status_code=404, detail="Analyse this company first")

    result = cache[ticker]
    answer = await query_index(
        question=req.question,
        index_data=result["index"],
        profile=result["profile"],
        model=result["model"],
        simulation=result["simulation"],
    )
    return {"answer": answer}


@app.get("/health")
def health():
    return {"status": "ok", "cached": list(cache.keys())}

@app.get("/compare/{ticker1}/{ticker2}")
async def compare(ticker1: str, ticker2: str):
    """Run pipeline on both companies and return side-by-side data."""
    ticker1, ticker2 = ticker1.upper(), ticker2.upper()

    for t in [ticker1, ticker2]:
        if t not in COMPANIES:
            raise HTTPException(status_code=404, detail=f"{t} not in preset list")

    import asyncio

    async def get_or_run(ticker):
        if ticker in cache:
            return cache[ticker]
        fin     = fetch_financials(ticker)
        wiki    = fetch_company_context(ticker)
        profile = build_profile(fin, wiki)
        model   = build_model(profile)
        sim     = simulate_funding(profile, model)
        advice  = await run_advisor(profile, model, sim)
        index   = build_index(profile, model, sim, advice)
        result  = {
            "ticker": ticker, "name": COMPANIES[ticker],
            "profile": profile, "model": model,
            "simulation": sim, "advice": advice, "index": index,
        }
        cache[ticker] = result
        return result

    results = await asyncio.gather(get_or_run(ticker1), get_or_run(ticker2))
    return {"company1": results[0], "company2": results[1]}

# ── Serve frontend ────────────────────────────────────────────────────────────
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")