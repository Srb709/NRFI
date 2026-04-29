from __future__ import annotations

def _clamp(v: float, lo: float = 0.35, hi: float = 0.70) -> float:
    return max(lo, min(hi, v))

def explain_prediction(input_features: dict) -> tuple[list[str], list[str]]:
    reasons, warnings = [], []
    if input_features.get('pitcher_walk_rate', 0.08) <= 0.08:
        reasons.append('Both starters project low walk risk early')
    if input_features.get('top_order_k_rate', 0.22) >= 0.22:
        reasons.append('Top of order has swing-and-miss risk')
    if input_features.get('weather_run_boost', 0.0) > 0.12:
        warnings.append('Weather needs update')
    if input_features.get('lineups_confirmed', False) is False:
        warnings.append('Lineups unconfirmed')
    return reasons or ['Baseline rule blend is near neutral.'], warnings

def classify_public_label(nrfi_probability: float, yrfi_probability: float, warnings: list[str]) -> str:
    if nrfi_probability >= 0.64 and len(warnings) <= 1: return 'Lab Favorite'
    if nrfi_probability >= 0.60: return 'Clean First Frame'
    if nrfi_probability >= 0.56: return 'Quiet Inning Candidate'
    if yrfi_probability >= 0.61: return 'YRFI Smoke'
    if yrfi_probability >= 0.56: return 'Chaos Zone' if len(warnings) >= 2 else 'Trap Watch'
    return 'Pass'

def predict_baseline(input_features: dict) -> dict:
    pitcher_safety_score = float(input_features.get('pitcher_safety_score', 0.55))
    offense_danger_score = float(input_features.get('offense_danger_score', 0.48))
    park_weather_score = float(input_features.get('park_weather_score', 0.50))
    recent_form_score = float(input_features.get('recent_form_score', 0.50))

    raw_nrfi = 0.52 + 0.22*(pitcher_safety_score-0.5) - 0.18*(offense_danger_score-0.5) - 0.12*(park_weather_score-0.5) + 0.08*(recent_form_score-0.5)
    nrfi_probability = _clamp(raw_nrfi)
    yrfi_probability = _clamp(1.0 - nrfi_probability)

    lean = 'NRFI' if nrfi_probability >= 0.55 else ('YRFI' if yrfi_probability >= 0.55 else 'PASS')
    confidence_tier = 'A' if max(nrfi_probability, yrfi_probability) >= 0.63 else ('B' if max(nrfi_probability, yrfi_probability) >= 0.58 else ('C' if lean != 'PASS' else 'PASS'))
    reasons, warnings = explain_prediction(input_features)
    return {
        'nrfi_probability': nrfi_probability,
        'yrfi_probability': yrfi_probability,
        'lean': lean,
        'public_label': classify_public_label(nrfi_probability, yrfi_probability, warnings),
        'confidence_tier': confidence_tier,
        'reasons': reasons,
        'warnings': warnings,
        'pitcher_safety_score': pitcher_safety_score,
        'offense_danger_score': offense_danger_score,
        'park_weather_score': park_weather_score,
        'recent_form_score': recent_form_score,
    }
