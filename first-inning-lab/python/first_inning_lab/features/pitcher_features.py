from __future__ import annotations


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def build_pitcher_features(pitcher_id, pitcher_name, season, as_of_date):
    warnings = []
    reasons = []
    data_available = pitcher_id is not None
    if not data_available:
        warnings.append("Missing probable pitcher stats; using neutral pitcher safety.")
    score = 0.50
    return {
        "pitcher_id": pitcher_id,
        "pitcher_name": pitcher_name,
        "data_available": data_available,
        "bb_rate": None,
        "k_rate": None,
        "k_minus_bb_rate": None,
        "xwoba_allowed": None,
        "barrel_rate_allowed": None,
        "hard_hit_rate_allowed": None,
        "first_inning_era": None,
        "first_inning_whip": None,
        "first_inning_sample": None,
        "days_rest": None,
        "pitcher_safety_score": _clamp(score),
        "warnings": warnings,
        "reasons": reasons or ["Pitcher fallback baseline used."],
    }
