def build_pitcher_features(pitcher_id,pitcher_name,season,as_of_date):
    warnings=[]; reasons=[]
    if not pitcher_id: warnings.append('Missing probable pitcher data')
    return {'pitcher_id':pitcher_id,'pitcher_name':pitcher_name,'data_available':bool(pitcher_id),'bb_rate':None,'k_rate':None,'k_minus_bb_rate':None,'xwoba_allowed':None,'barrel_rate_allowed':None,'hard_hit_rate_allowed':None,'first_inning_era':None,'first_inning_whip':None,'first_inning_sample':None,'days_rest':None,'pitcher_safety_score':0.5,'warnings':warnings,'reasons':reasons or ['Neutral pitcher baseline due to limited free data.']}
