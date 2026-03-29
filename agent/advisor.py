# agent/advisor.py
import os
import json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"


async def run_advisor(profile: dict, model: dict, simulation: dict) -> dict:
    """
    4-step reasoning chain. Each step is a separate Groq call
    so the thinking is observable and logged — not one opaque prompt.
    """
    ticker = profile["ticker"]
    print(f"\n[Advisor] Starting 4-step reasoning for {ticker}...")

    snapshot = _build_snapshot(profile, model, simulation)

    # Health analysis
    print(f"[Advisor] Step 1/4 — Analysing company health...")
    health_analysis = _call_groq(
        system="You are a senior equity analyst. Be concise, specific, and grounded in the numbers provided. No generic statements.",
        user=f"""Analyse the financial health of {ticker} based on this data:

{snapshot}

Write 3-4 sentences covering:
- What the health scores tell you
- Whether the margins and growth are strong or concerning
- Any risk flags and what they mean in practice

Be specific to these numbers, not generic."""
    )

    # Risk evaluation 
    print(f"[Advisor] Step 2/4 — Evaluating risks...")
    risk_evaluation = _call_groq(
        system="You are a credit risk analyst. Be direct and specific. Reference actual figures.",
        user=f"""Evaluate the key risks for {ticker} given:

{snapshot}

Previous health analysis:
{health_analysis}

Write 2-3 sentences on:
- The most material risks (reference the actual numbers)
- Whether the balance sheet can absorb a downside scenario
- One specific scenario where things go wrong"""
    )

    # Simulation interpretation
    print(f"[Advisor] Step 3/4 — Interpreting funding simulation...")
    sim_scores = simulation["scores"]
    recommended = simulation["recommended"]

    simulation_interpretation = _call_groq(
        system="You are a corporate finance advisor at an investment bank. Reference the actual scores and numbers.",
        user=f"""Interpret the funding simulation results for {ticker}:

Funding amount: ${simulation['funding_amount']/1e9:.1f}B
Scores — Equity: {sim_scores['equity']}/100 | Debt: {sim_scores['debt']}/100 | Buyback: {sim_scores['buyback']}/100
Model recommended: {recommended.upper()}

Company context:
{snapshot}

Write 3-4 sentences explaining:
- Why the scores came out this way for this specific company
- What the recommended option means in practice
- Any important caveats or conditions on the recommendation"""
    )

    # Final recommendation
    print(f"[Advisor] Step 4/4 — Generating final recommendation...")
    final_recommendation = _call_groq(
        system="You are a chief financial advisor delivering a board-level recommendation. Be decisive, specific, and structured.",
        user=f"""Based on the full analysis of {ticker}, deliver a final funding and strategic recommendation.

Health analysis: {health_analysis}
Risk evaluation: {risk_evaluation}
Simulation interpretation: {simulation_interpretation}

Financial snapshot:
{snapshot}

Structure your response as:
RECOMMENDATION: [one clear sentence]
RATIONALE: [2-3 sentences grounded in the numbers]
CONDITIONS: [1-2 sentences on what must be true for this to hold]
WHAT TO WATCH: [one risk or metric to monitor]

Be specific to {ticker}, not generic."""
    )

    print(f"[Advisor] ✓ All 4 steps complete for {ticker}")

    return {
        "ticker":                    ticker,
        "steps": {
            "health_analysis":           health_analysis,
            "risk_evaluation":           risk_evaluation,
            "simulation_interpretation": simulation_interpretation,
            "final_recommendation":      final_recommendation,
        },
        "recommended_option":        recommended,
        "confidence":                _score_confidence(profile, simulation),
        "disclaimer":                "This output is for educational purposes only and does not constitute investment advice.",
    }


def _call_groq(system: str, user: str) -> str:
    """Single Groq call — synchronous, wrapped for simplicity."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system",  "content": system},
                {"role": "user",    "content": user},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Advisor] ✗ Groq call failed: {e}")
        return f"Analysis unavailable: {e}"


def _build_snapshot(profile: dict, model: dict, simulation: dict) -> str:
    """Compact text snapshot of all key numbers — fed into every prompt."""
    rev     = profile.get("revenue", [])
    inc     = profile.get("net_income", [])
    health  = profile.get("health", {})
    flags   = profile.get("risk_flags", [])
    proj    = model["scenarios"]
    years   = model["projection_years"]

    return f"""
Company: {profile['ticker']} | {profile.get('sector')} | {profile.get('industry')}
Description: {profile.get('description', '')[:200]}

Financials (most recent year):
  Revenue:       ${rev[-1]/1e9:.1f}B  (4yr avg growth: {profile['avg_rev_growth']:.1%})
  Net income:    ${inc[-1]/1e9:.1f}B
  Profit margin: {profile['profit_margin']:.1%}
  FCF margin:    {profile['fcf_margin']:.1%}
  Cash:          ${profile['cash']/1e9:.1f}B
  Total debt:    ${profile['debt']/1e9:.1f}B
  Market cap:    ${profile['market_cap']/1e9:.1f}B
  P/E ratio:     {profile.get('pe_ratio') or 'N/A'}
  Beta:          {profile.get('beta') or 'N/A'}

Health scores (0–100):
  Overall: {health.get('overall')} | Profitability: {health.get('profitability')} | 
  Growth: {health.get('growth')} | Stability: {health.get('stability')} | Leverage: {health.get('leverage')}

Risk flags: {', '.join(flags) if flags else 'None identified'}
Funding recommendation: {simulation['recommended'].upper()} | Confidence: {_score_confidence(profile, simulation)}
5-year revenue projections:
  Base:     ${proj['base']['revenue'][-1]/1e9:.1f}B by {years[-1]} (growth: {proj['base']['growth']:.1%}/yr)
  Upside:   ${proj['upside']['revenue'][-1]/1e9:.1f}B by {years[-1]} (growth: {proj['upside']['growth']:.1%}/yr)
  Downside: ${proj['downside']['revenue'][-1]/1e9:.1f}B by {years[-1]} (growth: {proj['downside']['growth']:.1%}/yr)
""".strip()


def _score_confidence(profile: dict, simulation: dict) -> str:
    """Simple confidence rating based on data quality and score spread."""
    scores = list(simulation["scores"].values())
    spread = max(scores) - min(scores)
    flags  = len(profile.get("risk_flags", []))
    rev    = profile.get("revenue", [])

    if len(rev) < 3:
        return "low"
    if spread > 30 and flags == 0:
        return "high"
    if spread > 15:
        return "medium-high"
    return "medium"