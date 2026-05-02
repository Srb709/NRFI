import json
from pathlib import Path
import pandas as pd
from first_inning_lab.pipelines.build_half_inning_training_dataset import run


def _write_input(path: Path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def test_one_game_creates_two_rows(tmp_path):
    inp=tmp_path/'in.csv'; _write_input(inp,[{"game_pk":1,"game_date":"2024-04-01","away_team_id":10,"home_team_id":20,"away_team":"A","home_team":"H","away_starting_pitcher_id":100,"home_starting_pitcher_id":200,"venue_id":1,"away_runs_1st":0,"home_runs_1st":1,"total_runs_1st":1,"nrfi_result":0}])
    out=tmp_path/'o.csv'; jout=tmp_path/'o.json'; md=tmp_path/'m.json'
    run(inp,out,jout,md)
    df=pd.read_csv(out)
    assert len(df)==2
    top=df[df.inning_half=='top'].iloc[0]; bot=df[df.inning_half=='bottom'].iloc[0]
    assert top.scored_binary==0 and bot.scored_binary==1
    assert top.batting_team_id==10 and bot.batting_team_id==20
    assert top.pitcher_id==200 and bot.pitcher_id==100


def test_no_same_game_leakage(tmp_path):
    inp=tmp_path/'in.csv'; _write_input(inp,[{"game_pk":1,"game_date":"2024-04-01","away_runs_1st":0,"home_runs_1st":1}])
    out=tmp_path/'o.csv'; run(inp,out,tmp_path/'o.json',tmp_path/'m.json')
    df=pd.read_csv(out)
    assert (df['batting_team_prior_sample_size'].fillna(0)==0).all()
    assert (df['pitcher_prior_sample_size'].fillna(0)==0).all()


def test_same_date_not_used_as_prior(tmp_path):
    rows=[{"game_pk":1,"game_date":"2024-04-01","away_team_id":1,"home_team_id":2,"away_runs_1st":0,"home_runs_1st":0},{"game_pk":2,"game_date":"2024-04-01","away_team_id":1,"home_team_id":2,"away_runs_1st":1,"home_runs_1st":0}]
    inp=tmp_path/'in.csv'; _write_input(inp,rows)
    out=tmp_path/'o.csv'; run(inp,out,tmp_path/'o.json',tmp_path/'m.json')
    df=pd.read_csv(out)
    assert (df['league_prior_half_inning_sample_size'].fillna(0)==0).all()


def test_metadata_written(tmp_path):
    inp=tmp_path/'in.csv'; _write_input(inp,[{"game_pk":1,"game_date":"2024-04-01","away_runs_1st":0,"home_runs_1st":0}])
    md=tmp_path/'m.json'; run(inp,tmp_path/'o.csv',tmp_path/'o.json',md)
    data=json.loads(md.read_text())
    assert 'games_read' in data and 'half_inning_rows_written' in data and 'no_leakage_rule' in data
