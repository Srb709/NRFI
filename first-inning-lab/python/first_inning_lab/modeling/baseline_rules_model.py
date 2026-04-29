from __future__ import annotations


def _clamp_probability(value: float, low: float = 0.35, high: float = 0.70) -> float:
    return max(low, min(high, value))


def predict_baseline(input_features: dict) -> dict:
    p = float(input_features.get("pitcher_safety_score", 0.5))
    o = float(input_features.get("offense_danger_score", 0.5))
    pw = float(input_features.get("park_weather_score", 0.5))
    c = float(input_features.get("certainty_score", input_features.get("data_quality_score", 0.5)))
    r = float(input_features.get("recent_form_score", 0.5))
    warnings = list(input_features.get("warnings", []))
    reasons = list(input_features.get("reasons", []))

    nrfi_probability = _clamp_probability(0.54 + 0.40 * (p - 0.5) - 0.30 * (o - 0.5) - 0.15 * (pw - 0.5) + 0.10 * (c - 0.5) + 0.05 * (r - 0.5))
    yrfi_probability = _clamp_probability(1 - nrfi_probability)
    lean = "NRFI" if nrfi_probability >= 0.55 else ("YRFI" if yrfi_probability >= 0.55 else "PASS")

    if c < 0.45:
        lean = "PASS"
        warnings.append("Forced PASS: low data quality.")
    if not input_features.get("starters_confirmed_or_probable", False):
        lean = "PASS"
        warnings.append("Forced PASS: missing probable starters.")
    if "precipitation_delay_risk" in input_features.get("weather_flags", []):
        lean = "PASS"
        warnings.append("Weather delay risk flag present.")
    if 0.47 <= nrfi_probability <= 0.53:
        lean = "PASS"
    if len(warnings) >= 3:
        lean = "PASS"

    max_prob = max(nrfi_probability, yrfi_probability)
    confidence_tier = "PASS" if lean == "PASS" else ("A" if max_prob >= 0.62 else ("B" if max_prob >= 0.58 else "C"))
    if (not input_features.get("lineups_confirmed", False)) or (not input_features.get("advanced_stats_available", False)):
        if confidence_tier == "A":
            confidence_tier = "B"
    if input_features.get("bullpen_or_opener_risk", False) and confidence_tier == "A":
        confidence_tier = "C"

    public_label = "Pass"
    if lean == "NRFI":
        major_missing = any("missing" in w.lower() or "forced pass" in w.lower() for w in warnings)
        if c >= 0.75 and input_features.get("starters_confirmed_or_probable", False) and not major_missing and confidence_tier == "A":
            public_label = "Lab Favorite"
        else:
            public_label = "Clean First Frame" if confidence_tier in ("A", "B") else "Quiet Inning Candidate"
    elif lean == "YRFI":
        public_label = "YRFI Smoke" if confidence_tier in ("A", "B") else "Slight Lean"

    return {
        "nrfi_probability": nrfi_probability,
        "yrfi_probability": yrfi_probability,
        "lean": lean,
        "public_label": public_label,
        "confidence_tier": confidence_tier,
        "reasons": reasons or ["Conservative baseline blend."],
        "warnings": warnings,
        "feature_breakdown": {
            "pitcher_safety_score": p,
            "offense_danger_score": o,
            "park_weather_score": pw,
            "certainty_score": c,
            "recent_form_score": r,
        },
        "data_quality_score": c,
    }
