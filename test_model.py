# test_model.py
from ingestion.fetch   import fetch_financials
from ingestion.wiki    import fetch_company_context
from processing.profile import build_profile
from modeling.model    import build_model
from simulation.simulator import simulate_funding

if __name__ == "__main__":
    ticker = "SPOT"

    fin     = fetch_financials(ticker)
    wiki    = fetch_company_context(ticker)
    profile = build_profile(fin, wiki)
    model   = build_model(profile)

    print("\n--- HEALTH SCORES ---")
    for k, v in profile["health"].items():
        print(f"  {k:15}: {v}")

    print(f"\n--- RISK FLAGS ---")
    print(f"  {profile['risk_flags'] or 'None'}")

    print(f"\n--- PROJECTIONS ({', '.join(model['projection_years'])}) ---")
    for scenario, data in model["scenarios"].items():
        rev_b = [f"${v/1e9:.0f}B" for v in data["revenue"]]
        print(f"  {scenario:10}: {' → '.join(rev_b)}")


sim = simulate_funding(profile, model)

print("\n--- FUNDING SIMULATION ---")
print(f"  Funding amount: ${sim['funding_amount']/1e9:.1f}B")
print(f"  Runway months:  {sim['runway_months']}")
print()
for name, opt in sim["options"].items():
    print(f"  {opt['label']:30} score: {opt['score']}/100")
    for pro in opt["pros"]: print(f"    + {pro}")
    for con in opt["cons"]: print(f"    - {con}")
    print()
print(f"  ★ Recommended: {sim['recommended'].upper()}")