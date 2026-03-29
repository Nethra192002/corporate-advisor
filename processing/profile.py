# processing/profile.py
import numpy as np
from sklearn.linear_model import LinearRegression


def _trend_growth(series):
    """Linear regression on revenue series — more accurate than simple average."""
    if len(series) < 2:
        return 0.0, 0.0, "stable"
    X = np.arange(len(series)).reshape(-1, 1)
    y = np.array(series, dtype=float)
    model = LinearRegression()
    model.fit(X, y)
    r2        = model.score(X, y)
    slope     = model.coef_[0]
    mean_rev  = np.mean(y)
    trend_rate = slope / mean_rev if mean_rev != 0 else 0.0
    if trend_rate > 0.02:   direction = "accelerating"
    elif trend_rate < -0.02: direction = "decelerating"
    else:                    direction = "stable"
    return float(trend_rate), float(r2), direction


def build_profile(financials: dict, wiki: dict) -> dict:
    ticker     = financials.get("ticker", "")
    print(f"[Profile] Building profile for {ticker}...")

    revenue    = financials.get("revenue", [])
    net_income = financials.get("net_income", [])
    fcf        = financials.get("free_cash_flow", [])
    cash       = financials.get("cash") or 0
    debt       = financials.get("total_debt") or 0
    market_cap = financials.get("market_cap") or 1
    beta       = financials.get("beta") or 1.0

    # ── ML: linear regression growth trend ──
    avg_rev_growth,    rev_r2,    rev_direction    = _trend_growth(revenue)
    avg_income_growth, income_r2, income_direction = _trend_growth(net_income)

    latest_revenue = revenue[-1]    if revenue    else 1
    latest_income  = net_income[-1] if net_income else 0
    latest_fcf     = fcf[-1]        if fcf        else 0

    profit_margin = latest_income / latest_revenue if latest_revenue else 0
    fcf_margin    = latest_fcf    / latest_revenue if latest_revenue else 0

    net_debt       = debt - cash
    debt_to_equity = (
        debt / financials.get("total_equity", debt)
        if financials.get("total_equity") else None
    )

    # ── Risk flags ──
    risk_flags = []
    if avg_rev_growth < 0:                         risk_flags.append("Declining revenue")
    if profit_margin < 0:                          risk_flags.append("Unprofitable")
    if 0 <= profit_margin < 0.05:                  risk_flags.append("Very thin margins")
    if net_debt > latest_revenue * 0.5:            risk_flags.append("High leverage")
    if beta and beta > 1.5:                        risk_flags.append("High volatility")
    if rev_direction == "decelerating":            risk_flags.append("Growth decelerating")
    if fcf_margin < 0:                             risk_flags.append("Negative free cash flow")

    # ── Health scores ──
    def clamp(val, lo=0, hi=100):
        return max(lo, min(hi, val))

    profitability_score = clamp(int(profit_margin * 300))
    growth_score        = clamp(int(avg_rev_growth * 400 + 50))
    stability_score     = clamp(int(100 - (beta or 1) * 30))
    leverage_score      = clamp(int(100 - (net_debt / latest_revenue) * 50)) if latest_revenue else 50

    overall_health = int(
        profitability_score * 0.35 +
        growth_score        * 0.30 +
        stability_score     * 0.20 +
        leverage_score      * 0.15
    )

    profile = {
        "ticker":            ticker,
        "name":              financials.get("sector", ticker),
        "sector":            financials.get("sector", "Unknown"),
        "industry":          financials.get("industry", "Unknown"),
        "country":           financials.get("country", "Unknown"),
        "description":       wiki.get("description", ""),
        "wiki_url":          wiki.get("wiki_url", ""),
        "market_cap":        market_cap,
        "revenue":           revenue,
        "revenue_dates":     financials.get("revenue_dates", []),
        "net_income":        net_income,
        "free_cash_flow":    fcf,
        "cash":              cash,
        "debt":              debt,
        "net_debt":          net_debt,
        "debt_to_equity":    debt_to_equity,
        "pe_ratio":          financials.get("pe_ratio"),
        "beta":              beta,
        "dividend_rate":     financials.get("dividend_rate"),
        "avg_rev_growth":    avg_rev_growth,
        "avg_income_growth": avg_income_growth,
        "profit_margin":     profit_margin,
        "fcf_margin":        fcf_margin,
        "rev_r2":            rev_r2,
        "rev_direction":     rev_direction,
        "risk_flags":        risk_flags,
        "health": {
            "overall":       overall_health,
            "profitability": profitability_score,
            "growth":        growth_score,
            "stability":     stability_score,
            "leverage":      leverage_score,
        },
        "anomaly": {},  # filled in by main.py after cache check
    }

    print(f"[Profile] ✓ {ticker} — health: {overall_health}/100, "
          f"growth: {avg_rev_growth:.1%} ({rev_direction}, R²={rev_r2:.2f}), "
          f"margin: {profit_margin:.1%}, flags: {risk_flags or 'none'}")

    return profile