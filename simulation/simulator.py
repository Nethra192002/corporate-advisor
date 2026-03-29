# simulation/simulator.py

def simulate_funding(profile: dict, model: dict) -> dict:
    """
    Simulate three funding options and score each one.
    All assumptions are explicit — no magic numbers hidden in logic.
    """
    ticker = profile.get("ticker", "")
    print(f"[Simulator] Running funding simulation for {ticker}...")

    # Core inputs
    latest_revenue  = profile["revenue"][-1] if profile["revenue"] else 0
    latest_income   = profile["net_income"][-1] if profile["net_income"] else 0
    cash            = profile.get("cash") or 0
    debt            = profile.get("debt") or 0
    market_cap      = profile.get("market_cap") or 1
    profit_margin   = profile.get("profit_margin") or 0
    avg_rev_growth  = profile.get("avg_rev_growth") or 0
    health          = profile["health"]["overall"]
    base_revenue_y5 = model["scenarios"]["base"]["revenue"][-1]

    # Assume annual operating cash burn ~ net income if negative, else 0
    annual_burn     = max(-latest_income, 0)
    runway_months   = (cash / (annual_burn / 12)) if annual_burn > 0 else 999

    # Funding amount = 10% of market cap, capped at $10B, floored at $100M
    funding_amount  = max(100e6, min(market_cap * 0.10, 10e9))

    # ── OPTION 1: Equity raise ──────────────────────────────────────────
    dilution_pct        = funding_amount / market_cap
    equity_growth_boost = 0.03   # assume deployment adds ~3% to growth
    equity_upside_rev   = base_revenue_y5 * (1 + equity_growth_boost)

    equity_score = 50
    if dilution_pct < 0.05:   equity_score += 20   # low dilution
    if profit_margin > 0.15:  equity_score -= 10   # profitable co shouldn't dilute
    if avg_rev_growth > 0.10: equity_score += 20   # high growth justifies equity
    if health >= 70:          equity_score += 10
    equity_score = max(0, min(100, equity_score))

    # ── OPTION 2: Debt raise ────────────────────────────────────────────
    interest_rate       = 0.055  # ~5.5% corporate bond rate
    annual_interest     = funding_amount * interest_rate
    interest_coverage   = latest_income / annual_interest if annual_interest else 999
    new_debt_ratio      = (debt + funding_amount) / latest_revenue if latest_revenue else 1
    debt_growth_boost   = 0.02
    debt_upside_rev     = base_revenue_y5 * (1 + debt_growth_boost)

    debt_score = 50
    if interest_coverage > 5:   debt_score += 25   # easily covers interest
    if interest_coverage > 10:  debt_score += 10   # very comfortably covered
    if new_debt_ratio < 0.5:    debt_score += 15   # low resulting leverage
    if profit_margin < 0.05:    debt_score -= 20   # thin margins can't service debt
    if avg_rev_growth < 0:      debt_score -= 15   # declining revenue is dangerous
    debt_score = max(0, min(100, debt_score))

    # ── OPTION 3: Buyback / retain ──────────────────────────────────────
    # Only makes sense if profitable and cash-rich
    buyback_yield   = (funding_amount / market_cap) * 100  # % of market cap retired
    buyback_score   = 50
    if profit_margin > 0.20:  buyback_score += 25
    if cash > debt:           buyback_score += 20
    if avg_rev_growth < 0.05: buyback_score += 10   # slow growth = return cash
    if avg_rev_growth > 0.10: buyback_score -= 20   # any meaningful growth = deploy capital
    if avg_rev_growth > 0.20: buyback_score -= 15   # high growth = deploy capital
    if health < 60:           buyback_score -= 20   # unhealthy co shouldn't buyback
    buyback_score = max(0, min(100, buyback_score))

    # ── Recommended option ──────────────────────────────────────────────
    scores = {
        "equity":  equity_score,
        "debt":    debt_score,
        "buyback": buyback_score,
    }
    recommended = max(scores, key=scores.get)

    simulation = {
        "ticker":          ticker,
        "funding_amount":  funding_amount,
        "runway_months":   round(runway_months, 1),
        "options": {
            "equity": {
                "label":           "Equity raise",
                "funding_amount":  funding_amount,
                "dilution_pct":    round(dilution_pct * 100, 2),
                "growth_boost":    equity_growth_boost,
                "projected_rev_y5": equity_upside_rev,
                "score":           equity_score,
                "pros": _equity_pros(dilution_pct, avg_rev_growth),
                "cons": _equity_cons(dilution_pct, profit_margin),
            },
            "debt": {
                "label":              "Debt financing",
                "funding_amount":     funding_amount,
                "interest_rate":      interest_rate,
                "annual_interest":    annual_interest,
                "interest_coverage":  round(interest_coverage, 1),
                "new_debt_ratio":     round(new_debt_ratio, 2),
                "growth_boost":       debt_growth_boost,
                "projected_rev_y5":   debt_upside_rev,
                "score":              debt_score,
                "pros": _debt_pros(interest_coverage, new_debt_ratio),
                "cons": _debt_cons(profit_margin, new_debt_ratio),
            },
            "buyback": {
                "label":         "Share buyback / retain cash",
                "funding_amount": funding_amount,
                "buyback_yield":  round(buyback_yield, 2),
                "score":          buyback_score,
                "pros": _buyback_pros(profit_margin, cash, debt),
                "cons": _buyback_cons(avg_rev_growth),
            },
        },
        "scores":      scores,
        "recommended": recommended,
    }

    print(f"[Simulator] ✓ {ticker} — funding: ${funding_amount/1e9:.1f}B | "
          f"scores → equity: {equity_score}, debt: {debt_score}, buyback: {buyback_score}")
    print(f"[Simulator]   Recommended: {recommended.upper()}")

    return simulation


# ── Helper functions for human-readable pros/cons ───────────────────────────

def _equity_pros(dilution, growth):
    pros = ["No interest payments", "Strengthens balance sheet"]
    if dilution < 0.05: pros.append("Low dilution at current valuation")
    if growth > 0.15:   pros.append("High growth justifies equity cost")
    return pros

def _equity_cons(dilution, margin):
    cons = []
    if dilution > 0.08: cons.append(f"Meaningful dilution ({dilution*100:.1f}%)")
    if margin > 0.15:   cons.append("Unnecessary for a profitable company")
    cons.append("Signals management may see stock as fairly/overvalued")
    return cons

def _debt_pros(coverage, debt_ratio):
    pros = ["No shareholder dilution", "Interest is tax-deductible"]
    if coverage > 5:    pros.append(f"Strong interest coverage ({coverage:.1f}x)")
    if debt_ratio < 0.4: pros.append("Resulting leverage remains manageable")
    return pros

def _debt_cons(margin, debt_ratio):
    cons = ["Fixed interest obligations"]
    if margin < 0.10:   cons.append("Thin margins reduce debt servicing comfort")
    if debt_ratio > 0.6: cons.append("Elevated resulting leverage ratio")
    return cons

def _buyback_pros(margin, cash, debt):
    pros = ["Returns value directly to shareholders", "Improves EPS"]
    if margin > 0.20:   pros.append("Strong profitability supports buybacks")
    if cash > debt:     pros.append("Net cash position — no dilution risk")
    return pros

def _buyback_cons(growth):
    cons = []
    if growth > 0.15:   cons.append("High-growth phase — capital better deployed in operations")
    cons.append("Does not raise new capital for expansion")
    return cons