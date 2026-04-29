from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
from first_inning_lab.data_sources.mlb_stats_api import get_schedule
from first_inning_lab.data_sources.weather_client import get_game_weather
from first_inning_lab.features.assemble_game_features import assemble_game_features
from first_inning_lab.storage.json_store import read_json, atomic_write_json


def _root(): return Path(__file__).resolve().parents[3]

def run(date: str):
    parks = {str(p.get("venue_id")): p for p in read_json(_root()/"data/reference/park_factors.json", default=[])}
    games = get_schedule(date)
    rows=[]
    counts={"probable_pitchers_missing":0,"pitcher_stats_missing":0,"team_offense_stats_missing":0,"park_factor_missing":0,"stadium_coordinates_missing":0,"weather_missing":0,"lineups_unconfirmed":0,"historical_dataset_missing":0,"historical_venue_factor_missing":0,"park_or_venue_signal_missing":0,"historical_team_profile_missing":0,"historical_pitcher_profile_missing":0,"historical_fallback_used":0}
    for g in games:
        park=parks.get(str(g.get("venue_id")),{})
        weather=get_game_weather(park.get("latitude"),park.get("longitude"),g.get("start_time") or "")
        feat=assemble_game_features(g,int(date[:4]),parks,weather)
        fs=feat.get("feature_status", {}); raw=feat.get("raw_features", {})
        blockers=[]
        def miss(flag,key,label):
            if not flag: counts[key]+=1; blockers.append(label)
        miss(fs.get("probable_pitchers_available"),"probable_pitchers_missing","probable_pitchers")
        miss(fs.get("pitcher_stats_available"),"pitcher_stats_missing","pitcher_stats")
        miss(fs.get("team_offense_stats_available"),"team_offense_stats_missing","team_offense")
        miss(fs.get("park_factor_available"),"park_factor_missing","park_factor")
        miss((raw.get("park") or {}).get("stadium_coordinates_available"),"stadium_coordinates_missing","stadium_coordinates")
        miss(fs.get("weather_available"),"weather_missing","weather")
        miss(fs.get("lineups_confirmed"),"lineups_unconfirmed","lineups")
        miss(fs.get("historical_first_inning_available"),"historical_dataset_missing","historical_dataset")
        miss(fs.get("historical_venue_factor_available"),"historical_venue_factor_missing","historical_venue")
        miss(fs.get("park_or_venue_signal_available"),"park_or_venue_signal_missing","park_or_venue_signal")
        miss((raw.get("historical_team_away") or {}).get("available") and (raw.get("historical_team_home") or {}).get("available"),"historical_team_profile_missing","historical_team_profile")
        miss((raw.get("historical_pitcher_away") or {}).get("available") and (raw.get("historical_pitcher_home") or {}).get("available"),"historical_pitcher_profile_missing","historical_pitcher_profile")
        historical_venue = raw.get("historical_venue") or {}
        historical_league = raw.get("historical_league") or {}
        if historical_venue.get("season_fallback_used") or historical_league.get("season_fallback_used"):
            counts["historical_fallback_used"] += 1
        rows.append({"game":g.get("game"),"game_id":g.get("game_id"),"requested_historical_season":historical_venue.get("requested_season", historical_league.get("requested_season")),"used_historical_season":historical_venue.get("used_season", historical_league.get("used_season")),"season_fallback_used":bool(historical_venue.get("season_fallback_used") or historical_league.get("season_fallback_used")),"historical_dataset_file_exists":"Historical first-inning dataset unavailable." not in (historical_league.get("warnings") or []),"historical_dataset_available":fs.get("historical_first_inning_available"),"historical_venue_factor_available":fs.get("historical_venue_factor_available"),"historical_venue_sample_size":historical_venue.get("sample_size"),"historical_team_profile_available":(raw.get("historical_team_away") or {}).get("available") and (raw.get("historical_team_home") or {}).get("available"),"historical_pitcher_profile_available":(raw.get("historical_pitcher_away") or {}).get("available") and (raw.get("historical_pitcher_home") or {}).get("available"),"park_or_venue_signal_available":fs.get("park_or_venue_signal_available"),"top_blockers":blockers})
    out={"generated_at":datetime.utcnow().isoformat()+"Z","date":date,"games":len(games),"counts":counts,"games_audit":rows}
    atomic_write_json(_root()/"data/live/today_data_audit.json",out)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--date', required=True); args=ap.parse_args(); run(args.date)
