from __future__ import annotations
import argparse, csv, json
from datetime import datetime, timedelta
from pathlib import Path
from first_inning_lab.data_sources.mlb_stats_api import get_schedule, get_linescore, get_game_feed


def _root(): return Path(__file__).resolve().parents[3]

def _daterange(start,end):
    d=start
    while d<=end:
        yield d
        d+=timedelta(days=1)

def run(start:str,end:str):
    s=datetime.fromisoformat(start).date(); e=datetime.fromisoformat(end).date()
    rows=[]; skipped=0
    for d in _daterange(s,e):
        for g in get_schedule(d.isoformat()):
            if g.get('status') in {'Postponed','Cancelled','Suspended'}:
                skipped+=1; continue
            ls=get_linescore(g['game_pk']); inn=(ls.get('innings') or [])
            if not inn: continue
            first=inn[0]; ar=first.get('away',{}).get('runs'); hr=first.get('home',{}).get('runs')
            if ar is None or hr is None: continue
            feed=get_game_feed(g['game_pk']); pd=((feed.get('gameData') or {}).get('probablePitchers') or {})
            rows.append({"game_pk":g['game_pk'],"date":g['game_date'],"away_team":g['away_team'],"home_team":g['home_team'],"away_team_id":g['away_team_id'],"home_team_id":g['home_team_id'],"venue_id":g['venue_id'],"venue_name":g['venue'],"away_starting_pitcher_name":(pd.get('away') or {}).get('fullName') or g.get('away_probable_pitcher'),"home_starting_pitcher_name":(pd.get('home') or {}).get('fullName') or g.get('home_probable_pitcher'),"away_starting_pitcher_id":(pd.get('away') or {}).get('id') or g.get('away_probable_pitcher_id'),"home_starting_pitcher_id":(pd.get('home') or {}).get('id') or g.get('home_probable_pitcher_id'),"away_runs_1st":ar,"home_runs_1st":hr,"total_runs_1st":int(ar)+int(hr),"nrfi_result":int(ar)+int(hr)==0,"yrfi_result":int(ar)+int(hr)>0,"final_away_runs":(ls.get('teams') or {}).get('away',{}).get('runs'),"final_home_runs":(ls.get('teams') or {}).get('home',{}).get('runs'),"game_status":g.get('status')})
    outdir=_root()/"data/historical"; outdir.mkdir(parents=True,exist_ok=True)
    with open(outdir/'first_inning_results.csv','w',newline='') as f:
        if rows:
            w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    json.dump(rows, open(outdir/'first_inning_results.json','w'), indent=2)
    json.dump({"generated_at":datetime.utcnow().isoformat()+"Z","start":start,"end":end,"games_written":len(rows),"games_skipped_status":skipped}, open(outdir/'historical_build_metadata.json','w'), indent=2)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--start', required=True); ap.add_argument('--end', required=True); a=ap.parse_args(); run(a.start,a.end)
