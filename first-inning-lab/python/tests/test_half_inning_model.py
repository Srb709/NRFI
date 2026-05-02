import pandas as pd
import pytest
from first_inning_lab.pipelines.train_half_inning_model import chronological_split, get_feature_columns, run


def _dataset(n=60):
    rows=[]
    for i in range(n):
        d=f"2024-04-{(i//2)%20+1:02d}"
        rows.append({"game_pk":i//2,"game_date":d,"inning_half":"top" if i%2==0 else "bottom","scored_binary":i%3==0,"total_runs_1st":1 if i%3==0 else 0,
        "batting_team_score_rate_smoothed":0.3,"pitcher_score_allowed_rate_smoothed":0.3,"venue_score_rate_smoothed":0.3,"league_prior_half_inning_score_rate":0.3,
        "batting_team_prior_sample_size":30,"pitcher_prior_sample_size":10,"venue_prior_sample_size":40,"league_prior_half_inning_sample_size":100,"is_home_batting_team":i%2,"half_inning_data_quality_score":1.0})
    return pd.DataFrame(rows)


def test_chronological_split_no_shuffle():
    df=_dataset()
    tr,te=chronological_split(df.assign(game_date=pd.to_datetime(df.game_date)))
    assert tr.game_date.max() < te.game_date.min()


def test_feature_columns_exclude_leaky_fields():
    cols=get_feature_columns(_dataset())
    assert 'scored_binary' not in cols and 'total_runs_1st' not in cols and 'game_nrfi_result' not in cols


def test_train_pipeline_writes_outputs(tmp_path):
    df=_dataset(); inp=tmp_path/'d.csv'; df.to_csv(inp,index=False)
    run(inp,tmp_path/'model')
    assert (tmp_path/'model/half_inning_model.joblib').exists()
    assert (tmp_path/'model/half_inning_model_coefficients.json').exists()


def test_handles_small_dataset_gracefully(tmp_path):
    df=_dataset(6); inp=tmp_path/'d.csv'; df.to_csv(inp,index=False)
    with pytest.raises(ValueError):
        run(inp,tmp_path/'model')
