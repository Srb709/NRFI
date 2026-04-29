from first_inning_lab.modeling.baseline_rules_model import predict_baseline


def test_range_and_fields():
    r = predict_baseline({})
    assert 0.35 <= r['nrfi_probability'] <= 0.70
    assert 0.35 <= r['yrfi_probability'] <= 0.70
    assert r['lean'] in {'NRFI', 'YRFI', 'PASS'}
    assert isinstance(r['reasons'], list)
    assert isinstance(r['warnings'], list)
    assert r['public_label'] in {'Lab Favorite','Clean First Frame','Quiet Inning Candidate','Slight Lean','Trap Watch','Chaos Zone','YRFI Smoke','Stay Away Spot','Pass'}
