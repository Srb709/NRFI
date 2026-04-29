from __future__ import annotations


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def build_offense_features(team_id, team_name, opponent_pitcher_hand, confirmed_lineup, season, as_of_date):
    lineup_confirmed = bool(confirmed_lineup)
    warnings = []
    if not lineup_confirmed:
        warnings.append("Missing confirmed lineup; offense danger set to neutral.")
    return {
        "team_name": team_name,
        "lineup_confirmed": lineup_confirmed,
        "top_order_available": lineup_confirmed,
        "top_order_obp": None,
        "top_order_bb_rate": None,
        "top_order_k_rate": None,
        "top_order_iso": None,
        "top_order_xwoba": None,
        "top_order_barrel_rate": None,
        "platoon_advantage_score": 0.50,
        "offense_danger_score": _clamp(0.50),
        "data_available": lineup_confirmed,
        "warnings": warnings,
        "reasons": ["Offense fallback baseline used."],
    }
