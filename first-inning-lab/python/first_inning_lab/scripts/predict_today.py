from first_inning_lab.modeling.baseline_rules_model import predict_game
print(predict_game({'season_bb_rate':0.07,'season_k_rate':0.24,'projected_top_3_obp':0.33,'weather_run_boost':0.0,'unconfirmed_lineups':True}))
