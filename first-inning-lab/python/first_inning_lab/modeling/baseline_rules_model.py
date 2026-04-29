from __future__ import annotations

from first_inning_lab.utils.collections import dedupe_preserve_order


def _clamp_probability(value: float, low: float = 0.35, high: float = 0.70) -> float:
    return max(low, min(high, value))


def _pass_output(reasons: list[str], warnings: list[str], data_quality: float, feature_status: dict) -> dict:
    return {
        "nrfi_probability": None,
        "yrfi_probability": None,
        "probability_available": False,
        "lean": "PASS",
        "public_label": "Data Incomplete",
        "confidence_tier": "PASS",
        "model_status": "pass_insufficient_data",
        "probability_quality": "unpriced",
        "reasons": dedupe_preserve_order(reasons),
        "warnings": dedupe_preserve_order(warnings),
        "feature_breakdown": {},
        "data_quality_score": round(float(data_quality), 3),
        "feature_status": feature_status,
    }


def predict_baseline(input_features: dict) -> dict:
    feature_status = input_features.get("feature_status", {})
    real = input_features.get("real_features", input_features)
    warnings = list(input_features.get("warnings", []))
    reasons = list(input_features.get("missing_data", []))
    dq = float(input_features.get("data_quality_score", 0))

    required = [
        (feature_status.get("probable_pitchers_available"), "Missing probable pitcher; model price withheld."),
        (feature_status.get("pitcher_stats_available"), "Pitcher stats unavailable; model price withheld."),
        (feature_status.get("team_offense_stats_available"), "Team offense stats unavailable; model price withheld."),
        (feature_status.get("park_factor_available"), "Park factor unavailable; model price withheld."),
        (dq >= 0.70, "Data quality below minimum threshold for pricing."),
    ]
    missing = [msg for ok, msg in required if not ok]
    if missing:
        return _pass_output(reasons + missing, warnings, dq, feature_status)

    p = real.get("pitcher_safety_score")
    o = real.get("offense_danger_score")
    pw = real.get("park_weather_score")
    if p is None or o is None or pw is None:
        return _pass_output(reasons + ["Required real features unavailable; model price withheld."], warnings, dq, feature_status)

    nrfi_probability = _clamp_probability(0.54 + 0.45 * (p - 0.5) - 0.40 * (o - 0.5) - 0.25 * (pw - 0.5))
    yrfi_probability = _clamp_probability(1 - nrfi_probability)
    lean = "NRFI" if nrfi_probability >= 0.55 else ("YRFI" if yrfi_probability >= 0.55 else "PASS")
    confidence_tier = "PASS" if lean == "PASS" else ("A" if max(nrfi_probability, yrfi_probability) >= 0.62 else "B")

    return {
        "nrfi_probability": nrfi_probability,
        "yrfi_probability": yrfi_probability,
        "probability_available": True,
        "lean": lean,
        "public_label": "Clean First Frame" if lean == "NRFI" else ("YRFI Smoke" if lean == "YRFI" else "Pass"),
        "confidence_tier": confidence_tier,
        "model_status": "priced",
        "probability_quality": "early_board",
        "reasons": dedupe_preserve_order(reasons or ["Real feature blend from current-season MLB data."]),
        "warnings": dedupe_preserve_order(warnings),
        "feature_breakdown": {
            "pitcher_safety_score": p,
            "offense_danger_score": o,
            "park_weather_score": pw,
            "recent_form_score": real.get("recent_form_score"),
        },
        "data_quality_score": round(dq, 3),
        "feature_status": feature_status,
    }
