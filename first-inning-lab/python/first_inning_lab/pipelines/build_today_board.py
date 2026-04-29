import argparse
from datetime import datetime
from pathlib import Path
from first_inning_lab.data_sources.mlb_stats_api import get_schedule
from first_inning_lab.data_sources.weather_client import get_game_weather
from first_inning_lab.features.pitcher_features import build_pitcher_features
from first_inning_lab.features.offense_features import build_offense_features
from first_inning_lab.features.park_weather_features import build_park_weather_features
from first_inning_lab.features.certainty_features import build_certainty_features
from first_inning_lab.features.matchup_features import combine_game_features
from first_inning_lab.modeling.baseline_rules_model import predict_baseline
from first_inning_lab.storage.json_store import atomic_write_json, read_json
from first_inning_lab.utils.dates import today_et

def run(date):
    games=get_schedule(date)
    parks={str(p.get('venue_id')):p for p in read_json(Path(__file__).resolve().parents[3]/'data/reference/park_factors.json',default=[])}
    preds=[]; statuses=[]
    for g in games:
        w=get_game_weather(None,None,g.get('start_time'))
        ap=build_pitcher_features(g.get('away_probable_pitcher_id'),g.get('away_probable_pitcher'),int(date[:4]),date)
        hp=build_pitcher_features(g.get('home_probable_pitcher_id'),g.get('home_probable_pitcher'),int(date[:4]),date)
        ao=build_offense_features(g.get('away_team_id'),g.get('away_team'),None,None,int(date[:4]),date)
        ho=build_offense_features(g.get('home_team_id'),g.get('home_team'),None,None,int(date[:4]),date)
        pw=build_park_weather_features(g,parks,w); c=build_certainty_features(g,ap,hp,ao,ho,w)
        pred=predict_baseline(combine_game_features(g,ap,hp,ao,ho,pw,c)); pred['game_id']=g['game_id']; pred['board_status']=c['board_status']; preds.append(pred); statuses.append(c['board_status'])
    s={'games':len(games),'nrfi_leans':sum(p['lean']=='NRFI' for p in preds),'yrfi_leans':sum(p['lean']=='YRFI' for p in preds),'passes':sum(p['lean']=='PASS' for p in preds),'low_confidence':sum(p.get('board_status')=='LOW_CONFIDENCE' for p in preds)}
    board={'generated_at':datetime.utcnow().isoformat()+'Z','date':date,'source':'free_local_pipeline','board_status':'MIXED' if len(set(statuses))>1 else (statuses[0] if statuses else 'EARLY'),'games':games,'predictions':preds,'summary':s}
    root=Path(__file__).resolve().parents[3]/'data/live'; atomic_write_json(root/'today_games.json',games); atomic_write_json(root/'today_predictions.json',preds); atomic_write_json(root/'today_board.json',board)
    print('First Inning Lab Board'); print(f'Date: {date}'); print(f"Games: {s['games']} NRFI: {s['nrfi_leans']} YRFI: {s['yrfi_leans']} PASS: {s['passes']}")

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--date'); a=ap.parse_args(); run(a.date or today_et())
