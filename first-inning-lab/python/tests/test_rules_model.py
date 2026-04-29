from first_inning_lab.modeling.baseline_rules_model import predict_baseline


def _base_input():
    return {
        "feature_status": {
            "probable_pitchers_available": True,
            "pitcher_stats_available": True,
            "team_offense_stats_available": True,
            "park_factor_available": True,
            "weather_available": True,
            "lineups_confirmed": False,
        },
        "real_features": {"pitcher_safety_score": 0.65, "offense_danger_score": 0.4, "park_weather_score": 0.45, "recent_form_score": None},
        "warnings": [],
        "missing_data": [],
        "data_quality_score": 0.8,
    }


def test_missing_pitcher_stats_returns_unpriced():
    x = _base_input(); x["feature_status"]["pitcher_stats_available"] = False
    out = predict_baseline(x)
    assert out["probability_available"] is False


def test_missing_team_offense_returns_unpriced():
    x = _base_input(); x["feature_status"]["team_offense_stats_available"] = False
    out = predict_baseline(x)
    assert out["probability_available"] is False


def test_null_features_not_replaced_with_neutral():
    x = _base_input(); x["real_features"]["pitcher_safety_score"] = None
    out = predict_baseline(x)
    assert out["nrfi_probability"] is None and out["yrfi_probability"] is None


def test_real_features_price_and_differ():
    a = predict_baseline(_base_input())
    b_in = _base_input(); b_in["real_features"]["pitcher_safety_score"] = 0.8
    b = predict_baseline(b_in)
    assert a["probability_available"] is True
    assert a["nrfi_probability"] != b["nrfi_probability"]


def test_missing_probable_pitcher_forces_pass():
    x = _base_input(); x["feature_status"]["probable_pitchers_available"] = False
    out = predict_baseline(x)
    assert out["lean"] == "PASS"
