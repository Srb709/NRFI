def build_certainty_features(game, away_pitcher_features, home_pitcher_features, away_offense_features, home_offense_features, weather):
    score=1.0; warnings=[]
    if not away_offense_features.get('lineup_confirmed') or not home_offense_features.get('lineup_confirmed'): score-=0.2; warnings.append('Unconfirmed lineups')
    if not game.get('away_probable_pitcher_id') or not game.get('home_probable_pitcher_id'): score-=0.35; warnings.append('Missing probable starter')
    if weather.get('source')=='neutral_fallback': score-=0.1; warnings.append('Weather fallback used')
    dq=max(0,min(1,score)); bs='FINAL' if dq>=0.8 else ('EARLY' if dq>=0.5 else 'LOW_CONFIDENCE')
    return {'lineups_confirmed':away_offense_features.get('lineup_confirmed') and home_offense_features.get('lineup_confirmed'),'starters_confirmed_or_probable':bool(game.get('away_probable_pitcher_id') and game.get('home_probable_pitcher_id')),'weather_available':weather.get('source')!='neutral_fallback','bullpen_or_opener_risk':not bool(game.get('away_probable_pitcher_id') and game.get('home_probable_pitcher_id')),'data_quality_score':dq,'board_status':bs,'warnings':warnings,'reasons':['Data quality score derived from lineup/starter/weather availability.']}
