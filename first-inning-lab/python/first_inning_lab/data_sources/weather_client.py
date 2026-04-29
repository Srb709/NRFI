from __future__ import annotations

import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _unavailable(summary: str, warning: str) -> dict:
    return {
        "available": False,
        "temperature_f": None,
        "wind_speed_mph": None,
        "wind_direction_degrees": None,
        "precipitation_probability": None,
        "weather_summary": summary,
        "weather_run_factor": None,
        "weather_flags": [],
        "source": "unavailable",
        "warnings": [warning],
    }


def get_game_weather(latitude: float | None, longitude: float | None, start_time: str) -> dict:
    if latitude is None or longitude is None:
        return _unavailable("No stadium coordinates.", "Weather unavailable: missing stadium coordinates.")
    try:
        game_dt = datetime.fromisoformat((start_time or "").replace("Z", "+00:00"))
    except ValueError:
        return _unavailable("Start time unparseable.", "Weather unavailable: game start time could not be parsed.")
    params = urlencode({"latitude": latitude, "longitude": longitude, "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,wind_direction_10m", "timezone": "UTC"})
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    req = Request(url, headers={"User-Agent": "FirstInningLab/1.0", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=10) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, HTTPError, URLError, json.JSONDecodeError, ValueError):
        return _unavailable("Open-Meteo request failed.", "Weather unavailable: Open-Meteo request failed.")

    hourly = payload.get("hourly", {}) if isinstance(payload, dict) else {}
    times = hourly.get("time") or []
    if not times:
        return _unavailable("Open-Meteo hourly data missing.", "Weather unavailable: Open-Meteo hourly timeline missing.")

    parsed_times = []
    for t in times:
        try:
            parsed_times.append(datetime.fromisoformat(f"{t}+00:00"))
        except ValueError:
            parsed_times.append(None)
    idx = min((i for i, d in enumerate(parsed_times) if d is not None), key=lambda i: abs((parsed_times[i] - game_dt).total_seconds()), default=None)
    if idx is None:
        return _unavailable("Open-Meteo times unparseable.", "Weather unavailable: hourly timestamps unparseable.")

    def _at(key):
        arr = hourly.get(key) or []
        return arr[idx] if idx < len(arr) else None

    temp_c = _at("temperature_2m")
    wind_kmh = _at("wind_speed_10m")
    precip = _at("precipitation_probability")
    wind_dir = _at("wind_direction_10m")
    temp_f = temp_c * 9 / 5 + 32 if temp_c is not None else None
    wind_mph = wind_kmh * 0.621371 if wind_kmh is not None else None
    run_factor = 1.0
    flags: list[str] = []
    if temp_f is not None and temp_f > 80:
        run_factor += 0.03
        flags.append("hot_weather_flag")
    if temp_f is not None and temp_f < 50:
        run_factor -= 0.03
        flags.append("cold_weather_flag")
    if precip is not None and precip > 40:
        run_factor += 0.02
        flags.append("precipitation_delay_risk")
    return {
        "available": True,
        "temperature_f": temp_f,
        "wind_speed_mph": wind_mph,
        "wind_direction_degrees": wind_dir,
        "precipitation_probability": precip,
        "weather_summary": f"Open-Meteo nearest hourly row at {times[idx]} UTC",
        "weather_run_factor": run_factor,
        "weather_flags": flags,
        "source": "open_meteo",
        "warnings": [],
    }
