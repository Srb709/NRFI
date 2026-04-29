import requests

def get_game_weather(latitude, longitude, start_time):
    neutral={'temperature_f':None,'wind_speed_mph':None,'wind_direction_degrees':None,'precipitation_probability':None,'weather_summary':'Neutral fallback weather','weather_run_factor':1.0,'weather_flags':[],'source':'neutral_fallback'}
    if latitude is None or longitude is None: return neutral
    try:
        r=requests.get('https://api.open-meteo.com/v1/forecast',params={'latitude':latitude,'longitude':longitude,'hourly':'temperature_2m,precipitation_probability,wind_speed_10m,wind_direction_10m','forecast_days':1},timeout=10)
        if r.status_code!=200: return neutral
        h=r.json().get('hourly',{})
        t=(h.get('temperature_2m') or [None])[0]; w=(h.get('wind_speed_10m') or [None])[0]; p=(h.get('precipitation_probability') or [None])[0]; d=(h.get('wind_direction_10m') or [None])[0]
        tf=(t*9/5+32) if t is not None else None
        flags=[]; rf=1.0
        if tf and tf>80: rf+=0.03; flags.append('hot_weather_flag')
        if tf and tf<50: rf-=0.03; flags.append('cold_weather_flag')
        if w and w>10: flags.append('wind_flag')
        if p and p>40: flags.append('precipitation_delay_risk'); rf+=0.02
        return {'temperature_f':tf,'wind_speed_mph':(w*0.621371 if w is not None else None),'wind_direction_degrees':d,'precipitation_probability':p,'weather_summary':'Open-Meteo hourly snapshot','weather_run_factor':rf,'weather_flags':flags,'source':'open_meteo'}
    except Exception:
        return neutral
