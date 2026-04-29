import argparse
from pathlib import Path
from first_inning_lab.data_sources.mlb_stats_api import get_first_inning_result
from first_inning_lab.storage.json_store import read_json, atomic_write_json
from first_inning_lab.utils.dates import today_et

def run(date):
    root=Path(__file__).resolve().parents[3]/'data/live'; board=read_json(root/'today_board.json',{})
    preds={p['game_id']:p for p in board.get('predictions',[])}; results=[]
    for g in board.get('games',[]):
        r=get_first_inning_result(g['game_pk']); lean=preds.get(g['game_id'],{}).get('lean','PASS'); res=r['result']
        outcome='PASS' if lean=='PASS' or res in ('PENDING','UNKNOWN') else ('W' if lean==res else 'L')
        results.append({**g,**r,'lean':lean,'outcome':outcome})
    atomic_write_json(root/'today_results.json',results); atomic_write_json(root/'public_record_updates.json',results)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--date'); a=p.parse_args(); run(a.date or today_et())
