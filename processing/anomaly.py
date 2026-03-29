# processing/anomaly.py
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def score_anomaly(current_profile: dict, all_cached: dict) -> dict:
    ticker = current_profile["ticker"]
    peers  = {k: v["profile"] for k, v in all_cached.items() if k != ticker}

    if len(peers) < 1:
        return {
            "anomaly_score":   0.0,
            "is_outlier":      False,
            "peer_position":   "run more companies to enable peer comparison",
            "peer_comparison": {},
        }

    def extract_features(p):
        return [
            p.get("profit_margin",   0) or 0,
            p.get("avg_rev_growth",  0) or 0,
            p.get("health", {}).get("stability",     50),
            p.get("health", {}).get("leverage",      50),
            p.get("health", {}).get("profitability", 50),
            p.get("beta", 1) or 1,
        ]

    all_profiles = {ticker: current_profile, **peers}
    tickers      = list(all_profiles.keys())
    features     = [extract_features(all_profiles[t]) for t in tickers]

    X        = np.array(features, dtype=float)
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf         = IsolationForest(contamination=0.2, random_state=42)
    clf.fit(X_scaled)
    scores      = clf.decision_function(X_scaled)
    predictions = clf.predict(X_scaled)

    current_idx   = tickers.index(ticker)
    current_score = float(scores[current_idx])
    is_outlier = bool(predictions[current_idx] == -1)

    score_dict = {tickers[i]: scores[i] for i in range(len(tickers))}
    ranked     = sorted(score_dict.items(), key=lambda x: x[1])
    rank       = [t for t, _ in ranked].index(ticker) + 1

    if is_outlier:
        peer_position = f"outlier — unusually {'strong' if current_score > 0 else 'weak'} vs {len(peers)} peers"
    elif rank == len(tickers):
        peer_position = f"strongest profile among {len(tickers)} companies"
    elif rank == 1:
        peer_position = f"weakest profile among {len(tickers)} companies"
    else:
        peer_position = f"rank {rank} of {len(tickers)} companies"

    feature_names    = ["profit_margin","avg_rev_growth","stability","leverage","profitability","beta"]
    current_features = extract_features(current_profile)
    peer_comparison  = {}
    for i, fname in enumerate(feature_names):
        peer_vals = [extract_features(peers[p])[i] for p in peers]
        peer_avg  = float(np.mean(peer_vals)) if peer_vals else 0
        diff      = current_features[i] - peer_avg
        better_raw = diff > 0 if fname != "beta" else diff < 0
        peer_comparison[fname] = {
            "current":  round(float(current_features[i]), 4),
            "peer_avg": round(float(peer_avg), 4),
            "diff":     round(float(diff), 4),
            "better":   bool(better_raw),
        }

    print(f"[Anomaly] ✓ {ticker} — outlier: {is_outlier}, position: {peer_position}")

    return {
        "anomaly_score":   round(current_score, 4),
        "is_outlier":      is_outlier,
        "peer_position":   peer_position,
        "peer_comparison": peer_comparison,
    }