from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score
from first_inning_lab.storage.json_store import atomic_write_json


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_half_inning_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Cannot train half-inning model because dataset is empty.")
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    return df.sort_values(["game_date", "game_pk", "inning_half"]).reset_index(drop=True)


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    base = ["batting_team_score_rate_smoothed","pitcher_score_allowed_rate_smoothed","venue_score_rate_smoothed","league_prior_half_inning_score_rate","batting_team_prior_sample_size","pitcher_prior_sample_size","venue_prior_sample_size","league_prior_half_inning_sample_size","is_home_batting_team","half_inning_data_quality_score"]
    opt = ["batting_team_prior_first_inning_score_rate","pitcher_prior_first_inning_score_allowed_rate","venue_prior_first_inning_score_rate"]
    return [c for c in (base + opt) if c in df.columns]


def chronological_split(df: pd.DataFrame, train_end: str | None = None, test_start: str | None = None):
    if train_end and test_start:
        train = df[df["game_date"] <= pd.to_datetime(train_end)]
        test = df[df["game_date"] >= pd.to_datetime(test_start)]
    else:
        dates = sorted(df["game_date"].dropna().unique())
        if len(dates) < 2:
            raise ValueError("Not enough unique dates to split train/test.")
        cut = max(1, int(len(dates) * 0.7))
        train_dates = set(dates[:cut]); test_dates = set(dates[cut:])
        train = df[df["game_date"].isin(train_dates)]
        test = df[df["game_date"].isin(test_dates)]
    if train.empty or test.empty:
        raise ValueError("Train/test split produced empty partition.")
    return train.copy(), test.copy()


def train_model(train_df: pd.DataFrame, feature_cols: list[str]):
    y = train_df["scored_binary"].astype(int)
    if y.nunique() < 2:
        raise ValueError("Cannot train half-inning model because training target has only one class.")
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    model.fit(train_df[feature_cols], y)
    return model


def _bucket_eval(probs, actuals, buckets):
    out=[]
    for label, lo, hi in buckets:
        mask=(probs>=lo) & ((probs<hi) if hi<1 else (probs<=1))
        p=probs[mask]; a=actuals[mask]
        avgp=float(np.mean(p)) if len(p) else None; avga=float(np.mean(a)) if len(a) else None
        err=(avgp-avga) if avgp is not None and avga is not None else None
        out.append({"bucket":label,"count":int(len(p)),"average_predicted_score_probability":avgp,"actual_score_rate":avga,"calibration_error":err,"absolute_calibration_error":abs(err) if err is not None else None})
    return out


def evaluate_half_innings(model, test_df, feature_cols):
    probs = model.predict_proba(test_df[feature_cols])[:,1]
    y = test_df["scored_binary"].astype(int).to_numpy()
    roc = roc_auc_score(y, probs) if len(np.unique(y)) > 1 else None
    deciles=[]
    ranked = pd.DataFrame({"p":probs,"y":y}).sort_values("p").reset_index(drop=True)
    ranked["decile"]=pd.qcut(ranked.index,10,labels=False,duplicates="drop")+1
    for d in sorted(ranked["decile"].unique()):
        g=ranked[ranked["decile"]==d]
        deciles.append({"decile":int(d),"count":int(len(g)),"min_predicted_score_probability":float(g["p"].min()),"max_predicted_score_probability":float(g["p"].max()),"average_predicted_score_probability":float(g["p"].mean()),"actual_score_rate":float(g["y"].mean())})
    top=deciles[-1]["actual_score_rate"] if deciles else None; bot=deciles[0]["actual_score_rate"] if deciles else None
    return probs, {"actual_score_rate": float(np.mean(y)), "average_predicted_score_probability": float(np.mean(probs)), "test_log_loss": float(log_loss(y, probs, labels=[0,1])), "test_brier_score": float(brier_score_loss(y, probs)), "test_roc_auc": None if roc is None else float(roc), "calibration_by_probability_bucket": _bucket_eval(probs,y,[("0-9",0,0.1),("10-19",0.1,0.2),("20-29",0.2,0.3),("30-39",0.3,0.4),("40-49",0.4,0.5),("50+",0.5,1.0)]), "decile_diagnostics": deciles, "top_decile_actual_score_rate": top, "bottom_decile_actual_score_rate": bot, "top_minus_bottom_actual_score_rate": (top-bot) if top is not None and bot is not None else None}


def evaluate_game_level_nrfi(test_df: pd.DataFrame, probs: np.ndarray):
    df=test_df.copy(); df["p_score"]=probs
    g=[]
    for game_pk, grp in df.groupby("game_pk"):
        if set(grp["inning_half"]) != {"top","bottom"}: continue
        top=float(grp[grp["inning_half"]=="top"]["p_score"].iloc[0]); bottom=float(grp[grp["inning_half"]=="bottom"]["p_score"].iloc[0])
        nrfi=(1-top)*(1-bottom); yrfi=1-nrfi; total=float(grp["total_runs_1st"].iloc[0]); actual_nrfi=int(total==0)
        g.append({"game_pk": game_pk,"game_date": grp["game_date"].iloc[0].strftime("%Y-%m-%d"),"top_score_probability":top,"bottom_score_probability":bottom,"nrfi_probability":nrfi,"yrfi_probability":yrfi,"actual_nrfi":actual_nrfi,"actual_yrfi":1-actual_nrfi,"total_runs_1st":total})
    gf=pd.DataFrame(g)
    if gf.empty: raise ValueError("No paired top/bottom test rows for game-level evaluation.")
    nrfi_y=gf["actual_nrfi"].to_numpy(); nrfi_p=gf["nrfi_probability"].to_numpy()
    buckets=_bucket_eval(nrfi_p,nrfi_y,[("35-39",0.35,0.40),("40-44",0.40,0.45),("45-49",0.45,0.50),("50-54",0.50,0.55),("55-59",0.55,0.60),("60-64",0.60,0.65),("65+",0.65,1.0)])
    return gf, {"games_evaluated": int(len(gf)),"actual_nrfi_rate": float(np.mean(nrfi_y)),"average_model_nrfi_probability": float(np.mean(nrfi_p)),"average_model_yrfi_probability": float(np.mean(gf["yrfi_probability"])),"nrfi_brier_score": float(brier_score_loss(nrfi_y,nrfi_p)),"nrfi_log_loss": float(log_loss(nrfi_y,nrfi_p,labels=[0,1])),"nrfi_calibration_by_bucket": buckets}


def run(input_path: Path, model_dir: Path, train_end=None, test_start=None):
    df=load_half_inning_dataset(input_path); feats=get_feature_columns(df)
    if len(df)<20: raise ValueError("Not enough rows to train half-inning model.")
    tr, te=chronological_split(df,train_end,test_start)
    model=train_model(tr,feats)
    probs, eval_half=evaluate_half_innings(model,te,feats)
    gf, eval_game=evaluate_game_level_nrfi(te,probs)
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir/"half_inning_model.joblib")
    coef=model.named_steps["clf"].coef_[0]; inter=float(model.named_steps["clf"].intercept_[0])
    coef_json={"intercept":inter,"coefficients":{k:float(v) for k,v in zip(feats,coef)}}
    atomic_write_json(model_dir/"half_inning_model_coefficients.json",coef_json)
    eval_json={"generated_at":datetime.now(timezone.utc).isoformat(),"input_file":str(input_path),"model_file":str(model_dir/"half_inning_model.joblib"),"train_rows":len(tr),"test_rows":len(te),"train_date_min":tr["game_date"].min().strftime("%Y-%m-%d"),"train_date_max":tr["game_date"].max().strftime("%Y-%m-%d"),"test_date_min":te["game_date"].min().strftime("%Y-%m-%d"),"test_date_max":te["game_date"].max().strftime("%Y-%m-%d"),"feature_names":feats,"target":"scored_binary",**eval_half,"coefficient_summary":coef_json}
    atomic_write_json(model_dir/"half_inning_model_evaluation.json",eval_json)
    game_json={"generated_at":datetime.now(timezone.utc).isoformat(),**eval_game,"nrfi_probability_deciles":[],"threshold_simulation":{},"sample_game_predictions":gf.head(25).to_dict("records")}
    atomic_write_json(model_dir/"half_inning_game_level_evaluation.json",game_json)
    print("Half-Inning Scoring Model")
    return {"train":tr,"test":te,"eval":eval_json,"game":game_json}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",default="data/historical/half_inning_training_dataset.csv"); ap.add_argument("--train-end"); ap.add_argument("--test-start")
    args=ap.parse_args(); root=_root(); run(root/args.input, root/"data/model", args.train_end, args.test_start)

if __name__=="__main__":
    main()
