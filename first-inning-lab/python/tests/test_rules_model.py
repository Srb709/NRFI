from first_inning_lab.modeling.baseline_rules_model import predict_game
def test_range_and_fields():
 r=predict_game({}); assert 0.35<=r['nrfi_probability']<=0.70 and r['reasons'] is not None and r['warnings'] is not None
