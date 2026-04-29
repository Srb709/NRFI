from __future__ import annotations


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def build_park_weather_features(game: dict, park_factors: dict, weather: dict) -> dict:
    park = park_factors.get(str(game.get("venue_id")), {}) if isinstance(park_factors, dict) else {}
    warnings, reasons, flags = [], [], []
    run_factor = park.get("run_factor") if park else None
    hr_factor = park.get("hr_factor") if park else None
    park_factor_available = run_factor is not None and hr_factor is not None
    stadium_coordinates_available = bool(park) and park.get("latitude") is not None and park.get("longitude") is not None
    weather_available = bool(weather) and weather.get("available") and weather.get("source") == "open_meteo"
    weather_run = weather.get("weather_run_factor") if weather_available else None

    if not park:
        warnings.append("Park factor unavailable; model price withheld.")
        reasons.append("No park reference entry for venue.")
    elif not park_factor_available:
        warnings.append("Park factor unavailable; model price withheld.")
        reasons.append("Park reference exists but run/hr factors are null.")

    if not weather_available:
        warnings.append("Weather unavailable; weather not included.")

    score = None
    if park_factor_available:
        score = _clamp(0.50 + (float(run_factor) - 1.0) * 0.25 + (float(hr_factor) - 1.0) * 0.20 + ((float(weather_run) - 1.0) * 0.40 if weather_run is not None else 0.0))

    return {
        "park_factor_available": park_factor_available,
        "weather_available": weather_available,
        "stadium_coordinates_available": stadium_coordinates_available,
        "park_weather_score": score,
        "park_run_factor": run_factor,
        "park_hr_factor": hr_factor,
        "weather_run_factor": weather_run,
        "flags": flags + (weather.get("weather_flags", []) if isinstance(weather, dict) else []),
        "warnings": warnings + (weather.get("warnings", []) if isinstance(weather, dict) else []),
        "reasons": reasons,
    }
