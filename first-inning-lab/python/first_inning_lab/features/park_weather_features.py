def build_park_weather_features(game, park_factors, weather):
    park=park_factors.get(str(game.get('venue_id')),{}) if isinstance(park_factors,dict) else {}
    run=float(park.get('run_factor',1.0)); hr=float(park.get('hr_factor',1.0)); wr=float(weather.get('weather_run_factor',1.0))
    score=max(0,min(1,0.5 + (run-1)*0.25 + (hr-1)*0.2 + (wr-1)*0.4))
    return {'park_run_factor':run,'park_hr_factor':hr,'weather_run_factor':wr,'park_weather_score':score,'flags':weather.get('weather_flags',[]),'warnings':[],'reasons':['Park/weather blended conservatively.']}
