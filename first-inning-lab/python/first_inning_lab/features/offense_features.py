def build_offense_features(team_id,team_name,opponent_pitcher_hand,confirmed_lineup,season,as_of_date):
    lineup_confirmed=bool(confirmed_lineup)
    warnings=[] if lineup_confirmed else ['Lineup not confirmed; using neutral offense fallback']
    return {'team_name':team_name,'lineup_confirmed':lineup_confirmed,'top_order_available':lineup_confirmed,'top_order_obp':None,'top_order_bb_rate':None,'top_order_k_rate':None,'top_order_iso':None,'top_order_xwoba':None,'top_order_barrel_rate':None,'platoon_advantage_score':0.5,'offense_danger_score':0.5,'warnings':warnings,'reasons':['Neutral offense baseline for V1 free board.']}
