from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


NEUTRAL = {
    "temperature_f": None,
    "wind_speed_mph": None,
    "wind_direction_degrees": None,
    "precipitation_probability": None,
    "weather_summary": "Neutral fallback weather",
    "weather_run_factor": 1.0,
    "weather_flags": [],
    "source": "neutral_fallback",
}


def get_game_weather(latitude: float | None, longitude: float | None, start_time: str) -> dict:
    if latitude is None or longitude is None:
        return dict(NEUTRAL)
    params = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,wind_direction_10m",
            "forecast_days": 1,
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    req = Request(url, headers={"User-Agent": "FirstInningLab/1.0", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=10) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, HTTPError, URLError, json.JSONDecodeError, ValueError):
        return dict(NEUTRAL)
    hourly = payload.get("hourly", {}) if isinstance(payload, dict) else {}
    temp_c = (hourly.get("temperature_2m") or [None])[0]
    wind_kmh = (hourly.get("wind_speed_10m") or [None])[0]
    precip = (hourly.get("precipitation_probability") or [None])[0]
    wind_dir = (hourly.get("wind_direction_10m") or [None])[0]
    temp_f = temp_c * 9 / 5 + 32 if temp_c is not None else None
    wind_mph = wind_kmh * 0.621371 if wind_kmh is not None else None
    flags: list[str] = []
    run_factor = 1.0
    if temp_f is not None and temp_f > 80:
        run_factor += 0.03
        flags.append("hot_weather_flag")
    if temp_f is not None and temp_f < 50:
        run_factor -= 0.03
        flags.append("cold_weather_flag")
    if wind_mph is not None and wind_mph > 10:
        flags.append("wind_flag")
    if precip is not None and precip > 40:
        run_factor += 0.02
        flags.append("precipitation_delay_risk")
    return {
        "temperature_f": temp_f,
        "wind_speed_mph": wind_mph,
        "wind_direction_degrees": wind_dir,
        "precipitation_probability": precip,
        "weather_summary": "Open-Meteo hourly snapshot",
        "weather_run_factor": run_factor,
        "weather_flags": flags,
        "source": "open_meteo",
    }
