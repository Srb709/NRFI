from first_inning_lab.features.pitcher_features import build_pitcher_features

def test_neutral():
    p=build_pitcher_features(None,None,2026,'2026-04-29')
    assert p['pitcher_safety_score']==0.5
