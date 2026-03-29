# rag/indexer.py
def build_index(profile: dict, model: dict, simulation: dict, advice: dict) -> list[dict]:
    ticker = profile["ticker"]
    rev    = profile.get("revenue", [])
    inc    = profile.get("net_income", [])
    proj   = model["scenarios"]
    years  = model["projection_years"]
    steps  = advice.get("steps", {})
    confidence = advice.get("confidence", "medium")
    recommended = simulation["recommended"]

    chunks = [
        {
            "topic": "company overview",
            "content": f"{ticker} operates in {profile.get('sector')} ({profile.get('industry')}). "
                       f"{profile.get('description', '')} "
                       f"Market cap: ${profile['market_cap']/1e9:.1f}B. "
                       f"Employees: {profile.get('employees', 'N/A')}."
        },
        {
            "topic": "revenue income financials",
            "content": f"{ticker} most recent revenue: ${rev[-1]/1e9:.1f}B. "
                       f"Net income: ${inc[-1]/1e9:.1f}B. "
                       f"Profit margin: {profile['profit_margin']:.1%}. "
                       f"FCF margin: {profile['fcf_margin']:.1%}. "
                       f"4-year average revenue growth: {profile['avg_rev_growth']:.1%}."
        },
        {
            "topic": "balance sheet cash debt leverage",
            "content": f"{ticker} holds ${profile['cash']/1e9:.1f}B cash and "
                       f"${profile['debt']/1e9:.1f}B total debt. "
                       f"Net debt: ${profile['net_debt']/1e9:.1f}B. "
                       f"Beta: {profile.get('beta')}. P/E ratio: {profile.get('pe_ratio') or 'N/A'}. "
                       f"Debt to equity: {profile.get('debt_to_equity') or 'N/A'}."
        },
        {
            "topic": "health scores overall profitability growth stability",
            "content": f"{ticker} health scores — Overall: {profile['health']['overall']}/100. "
                       f"Profitability: {profile['health']['profitability']}. "
                       f"Growth: {profile['health']['growth']}. "
                       f"Stability: {profile['health']['stability']}. "
                       f"Leverage: {profile['health']['leverage']}. "
                       f"Risk flags: {', '.join(profile['risk_flags']) or 'none'}."
        },
        {
            "topic": "financial projections forecast scenarios base upside downside",
            "content": f"{ticker} 5-year projections to {years[-1]}: "
                       f"Base case ${proj['base']['revenue'][-1]/1e9:.1f}B "
                       f"at {proj['base']['growth']:.1%} annual growth. "
                       f"Upside ${proj['upside']['revenue'][-1]/1e9:.1f}B "
                       f"at {proj['upside']['growth']:.1%}. "
                       f"Downside ${proj['downside']['revenue'][-1]/1e9:.1f}B "
                       f"at {proj['downside']['growth']:.1%}."
        },
        {
            "topic": "funding simulation equity debt buyback recommendation score confidence",
            "content": f"{ticker} funding simulation on ${simulation['funding_amount']/1e9:.1f}B: "
                       f"Equity score {simulation['scores']['equity']}/100, "
                       f"Debt score {simulation['scores']['debt']}/100, "
                       f"Buyback score {simulation['scores']['buyback']}/100. "
                       f"Recommended option: {recommended.upper()}. "
                       f"Confidence level: {confidence}. "
                       f"Confidence is rated {confidence} based on data coverage, "
                       f"score spread of {max(simulation['scores'].values()) - min(simulation['scores'].values())} points, "
                       f"and {len(profile.get('risk_flags', []))} risk flags identified."
        },
        {
            "topic": "risk flags volatility concerns warnings",
            "content": f"{ticker} risk assessment: "
                       f"Flags identified: {', '.join(profile['risk_flags']) if profile['risk_flags'] else 'none'}. "
                       f"Beta: {profile.get('beta')} — {'high volatility' if (profile.get('beta') or 0) > 1.5 else 'moderate volatility'}. "
                       f"Runway months: {simulation.get('runway_months', 'N/A')}."
        },
        {
            "topic": "AI health analysis",
            "content": steps.get("health_analysis", "")
        },
        {
            "topic": "AI risk evaluation danger concern",
            "content": steps.get("risk_evaluation", "")
        },
        {
            "topic": "AI funding interpretation simulation",
            "content": steps.get("simulation_interpretation", "")
        },
        {
            "topic": "AI final recommendation advisory confidence conclusion",
            "content": f"Final recommendation for {ticker}: "
                       f"{steps.get('final_recommendation', '')} "
                       f"Overall confidence: {confidence}. "
                       f"Disclaimer: {advice.get('disclaimer', '')}"
        },
    ]

    print(f"[Indexer] ✓ Built {len(chunks)} chunks for {ticker}")
    return chunks