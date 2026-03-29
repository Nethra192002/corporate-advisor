# modeling/model.py
from config import MODEL_ASSUMPTIONS


def build_model(profile: dict) -> dict:
    ticker = profile.get("ticker", "")
    print(f"[Model] Building financial model for {ticker}...")

    assumptions  = MODEL_ASSUMPTIONS
    years        = assumptions["projection_years"]
    base_rev     = profile["revenue"][-1] if profile["revenue"] else 0
    hist_growth  = profile["avg_rev_growth"]
    hist_margin  = profile["profit_margin"]

    # Growth rate per scenario
    base_growth     = min(hist_growth + assumptions["base_growth_premium"], 0.50)
    upside_growth   = min(hist_growth + assumptions["upside_growth_premium"], 0.60)
    downside_growth = max(hist_growth * assumptions["downside_growth_cut"], -0.15)

    # Floor
    downside_growth = max(downside_growth, -0.15)

    # Ceiling
    upside_growth   = min(upside_growth, 0.60)

    def project(start, growth_rate, n_years):
        result = []
        val = start
        for _ in range(n_years):
            val = val * (1 + growth_rate)
            result.append(round(val, 2))
        return result

    base_revenue     = project(base_rev, base_growth,     years)
    upside_revenue   = project(base_rev, upside_growth,   years)
    downside_revenue = project(base_rev, downside_growth, years)

    # Net income projections
    base_income     = [round(r * hist_margin,         2) for r in base_revenue]
    upside_income   = [round(r * (hist_margin + 0.03), 2) for r in upside_revenue]
    downside_income = [round(r * (hist_margin - 0.03), 2) for r in downside_revenue]

    # Projection year labels
    last_hist_year  = int(profile["revenue_dates"][-1]) if profile.get("revenue_dates") else 2024
    proj_years      = [str(last_hist_year + i + 1) for i in range(years)]

    model = {
        "ticker":             ticker,
        "base_rev_year":      base_rev,
        "hist_growth":        hist_growth,
        "assumptions": {
            "base_growth":      base_growth,
            "upside_growth":    upside_growth,
            "downside_growth":  downside_growth,
            "projection_years": years,
        },
        "projection_years":   proj_years,
        "scenarios": {
            "base": {
                "revenue":    base_revenue,
                "net_income": base_income,
                "growth":     base_growth,
            },
            "upside": {
                "revenue":    upside_revenue,
                "net_income": upside_income,
                "growth":     upside_growth,
            },
            "downside": {
                "revenue":    downside_revenue,
                "net_income": downside_income,
                "growth":     downside_growth,
            },
        },
    }

    print(f"[Model] ✓ {ticker} — "
          f"base growth: {base_growth:.1%}, "
          f"upside: {upside_growth:.1%}, "
          f"downside: {downside_growth:.1%}")
    print(f"[Model]   Base revenue Y5: ${base_revenue[-1]/1e9:.1f}B | "
          f"Upside: ${upside_revenue[-1]/1e9:.1f}B | "
          f"Downside: ${downside_revenue[-1]/1e9:.1f}B")

    return model