from first_inning_lab.modeling.baseline_rules_model import predict_baseline

def test_bounds_and_pass():
    o=predict_baseline({'data_quality_score':0.4,'starters_confirmed_or_probable':False})
    assert 0.35<=o['nrfi_probability']<=0.7 and o['lean']=='PASS' and 'feature_breakdown' in o
