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
    counts={"probable_pitchers_missing":0,"pitcher_stats_missing":0,"team_offense_stats_missing":0,"park_factor_missing":0,"stadium_coordinates_missing":0,"weather_missing":0,"lineups_unconfirmed":0}
    for g in games:
        park=parks.get(str(g.get("venue_id")),{})
        weather=get_game_weather(park.get("latitude"),park.get("longitude"),g.get("start_time") or "")
        feat=assemble_game_features(g,int(date[:4]),parks,weather)
        fs=feat["feature_status"]
        blockers=[]
        if not fs["probable_pitchers_available"]: counts["probable_pitchers_missing"]+=1; blockers.append("probable_pitchers")
        if not fs["pitcher_stats_available"]: counts["pitcher_stats_missing"]+=1; blockers.append("pitcher_stats")
        if not fs["team_offense_stats_available"]: counts["team_offense_stats_missing"]+=1; blockers.append("team_offense")
        if not fs["park_factor_available"]: counts["park_factor_missing"]+=1; blockers.append("park_factor")
        if not feat["raw_features"]["park"].get("stadium_coordinates_available"): counts["stadium_coordinates_missing"]+=1; blockers.append("stadium_coordinates")
        if not fs["weather_available"]: counts["weather_missing"]+=1; blockers.append("weather")
        if not fs["lineups_confirmed"]: counts["lineups_unconfirmed"]+=1; blockers.append("lineups")
        rows.append({"game":g.get("game"),"game_id":g.get("game_id"),"venue_id":g.get("venue_id"),"venue_name":g.get("venue"),"probable_pitchers_available":fs["probable_pitchers_available"],"pitcher_stats_available":fs["pitcher_stats_available"],"team_offense_stats_available":fs["team_offense_stats_available"],"park_factor_available":fs["park_factor_available"],"stadium_coordinates_available":feat["raw_features"]["park"].get("stadium_coordinates_available"),"weather_available":fs["weather_available"],"lineups_confirmed":fs["lineups_confirmed"],"top_blockers":blockers})
    out={"generated_at":datetime.utcnow().isoformat()+"Z","date":date,"games":len(games),"counts":counts,"games_audit":rows}
    atomic_write_json(_root()/"data/live/today_data_audit.json",out)
    print(f"Audit date {date} games={len(games)}")
    for r in rows:
        print(f"{r['game']} | {r['game_id']} | park={r['park_factor_available']} wx={r['weather_available']} lu={r['lineups_confirmed']} blockers={','.join(r['top_blockers']) or 'none'}")

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--date', required=True); args=ap.parse_args(); run(args.date)
