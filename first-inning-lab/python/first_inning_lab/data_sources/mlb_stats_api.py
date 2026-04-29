from __future__ import annotations
import requests
BASE='https://statsapi.mlb.com/api/v1'
HEADERS={'User-Agent':'FirstInningLab/1.0 (free local engine)'}

def _get(url,params=None):
    try:
        r=requests.get(url,params=params,headers=HEADERS,timeout=12)
        if r.status_code!=200: return {}
        return r.json()
    except Exception:
        return {}

def normalize_game(g):
    teams=g.get('teams',{})
    away=teams.get('away',{}); home=teams.get('home',{})
    return {
      'game_id': str(g.get('gamePk','')),'game_pk': g.get('gamePk'), 'game_date': (g.get('gameDate') or '')[:10],
      'start_time': g.get('gameDate'), 'away_team': away.get('team',{}).get('name'), 'home_team': home.get('team',{}).get('name'),
      'away_team_id': away.get('team',{}).get('id'),'home_team_id': home.get('team',{}).get('id'),'venue': g.get('venue',{}).get('name'),
      'venue_id': g.get('venue',{}).get('id'),'status': g.get('status',{}).get('detailedState','Unknown'),
      'away_probable_pitcher': away.get('probablePitcher',{}).get('fullName'),'home_probable_pitcher': home.get('probablePitcher',{}).get('fullName'),
      'away_probable_pitcher_id': away.get('probablePitcher',{}).get('id'),'home_probable_pitcher_id': home.get('probablePitcher',{}).get('id'),'source':'mlb_stats_api'
    }

def get_schedule(date:str):
    d=_get(f'{BASE}/schedule',{'sportId':1,'date':date,'hydrate':'probablePitcher,venue'})
    return [normalize_game(g) for ds in d.get('dates',[]) for g in ds.get('games',[])]

def get_game_feed(game_pk): return _get(f'{BASE}.1/game/{game_pk}/feed/live')
def get_linescore(game_pk): return _get(f'{BASE}/game/{game_pk}/linescore')
def get_boxscore(game_pk): return _get(f'{BASE}/game/{game_pk}/boxscore')

def get_first_inning_result(game_pk):
    ls=get_linescore(game_pk)
    innings=ls.get('innings') or []
    if not innings: return {'game_pk':int(game_pk),'away_runs_1st':None,'home_runs_1st':None,'total_runs_1st':None,'result':'UNKNOWN','graded':False}
    i1=innings[0]
    a=i1.get('away',{}).get('runs'); h=i1.get('home',{}).get('runs')
    if a is None or h is None: return {'game_pk':int(game_pk),'away_runs_1st':a,'home_runs_1st':h,'total_runs_1st':None,'result':'PENDING','graded':False}
    t=a+h; res='NRFI' if t==0 else 'YRFI'
    return {'game_pk':int(game_pk),'away_runs_1st':a,'home_runs_1st':h,'total_runs_1st':t,'result':res,'graded':True}
