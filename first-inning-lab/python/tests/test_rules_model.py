from first_inning_lab.modeling.baseline_rules_model import predict_baseline


def test_probability_bounds():
    out = predict_baseline({})
    assert 0.35 <= out["nrfi_probability"] <= 0.7


def test_forced_pass_rules():
    out = predict_baseline({"data_quality_score": 0.4, "starters_confirmed_or_probable": False})
    assert out["lean"] == "PASS"


def test_a_tier_blocked_missing_inputs():
    out = predict_baseline({"lineups_confirmed": False, "advanced_stats_available": False, "starters_confirmed_or_probable": True, "data_quality_score": 0.9, "certainty_score": 0.9, "pitcher_safety_score": 0.8, "offense_danger_score": 0.3, "park_weather_score": 0.4})
    assert out["confidence_tier"] != "A"


def test_output_shape():
    out = predict_baseline({})
    assert "feature_breakdown" in out and "data_quality_score" in out
