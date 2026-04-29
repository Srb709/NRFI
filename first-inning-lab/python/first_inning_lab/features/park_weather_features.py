from __future__ import annotations


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def build_park_weather_features(game: dict, park_factors: dict, weather: dict) -> dict:
    park = park_factors.get(str(game.get("venue_id")), {}) if isinstance(park_factors, dict) else {}
    run_factor = float(park.get("run_factor", 1.0))
    hr_factor = float(park.get("hr_factor", 1.0))
    weather_run = float((weather or {}).get("weather_run_factor", 1.0))
    score = _clamp(0.50 + (run_factor - 1.0) * 0.25 + (hr_factor - 1.0) * 0.20 + (weather_run - 1.0) * 0.40)
    warnings = []
    if not weather or weather.get("source") == "neutral_fallback":
        warnings.append("Weather unavailable; neutral park/weather fallback used.")
    return {
        "park_run_factor": run_factor,
        "park_hr_factor": hr_factor,
        "weather_run_factor": weather_run,
        "park_weather_score": score,
        "flags": (weather or {}).get("weather_flags", []),
        "warnings": warnings,
        "reasons": ["Park/weather score blended conservatively."],
        "data_available": weather.get("source") != "neutral_fallback" if weather else False,
    }
