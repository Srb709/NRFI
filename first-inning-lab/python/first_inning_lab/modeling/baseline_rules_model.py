from __future__ import annotations

def _clamp(v: float, lo: float = 0.35, hi: float = 0.70) -> float:
    return max(lo, min(hi, v))

def predict_baseline(input_features: dict) -> dict:
    p=float(input_features.get('pitcher_safety_score',0.5)); o=float(input_features.get('offense_danger_score',0.5)); pw=float(input_features.get('park_weather_score',0.5)); c=float(input_features.get('certainty_score',input_features.get('data_quality_score',0.5))); r=float(input_features.get('recent_form_score',0.5))
    warnings=list(input_features.get('warnings',[])); reasons=list(input_features.get('reasons',[]))
    nrfi=_clamp(0.54 + 0.40*(p-0.5) - 0.30*(o-0.5) - 0.15*(pw-0.5) + 0.10*(c-0.5) + 0.05*(r-0.5))
    yrfi=_clamp(1-nrfi)
    lean='NRFI' if nrfi>=0.55 else ('YRFI' if yrfi>=0.55 else 'PASS')
    if c<0.45 or not input_features.get('starters_confirmed_or_probable',True): lean='PASS'; warnings.append('PASS forced by low data quality or missing probable starters')
    if 0.47<=nrfi<=0.53 or (abs(nrfi-yrfi)<0.03 and len(warnings)>=3): lean='PASS'
    if 'precipitation_delay_risk' in input_features.get('weather_flags',[]): warnings.append('Weather delay risk flag'); lean='PASS'
    conf='PASS' if lean=='PASS' else ('A' if max(nrfi,yrfi)>=0.62 and c>=0.75 else ('B' if max(nrfi,yrfi)>=0.58 else 'C'))
    if input_features.get('bullpen_or_opener_risk') and conf=='A': conf='C'
    label='Pass' if lean=='PASS' else ('Lab Favorite' if lean=='NRFI' and conf=='A' and input_features.get('lineups_confirmed') else ('Clean First Frame' if lean=='NRFI' else 'YRFI Smoke'))
    return {'nrfi_probability':nrfi,'yrfi_probability':yrfi,'lean':lean,'public_label':label,'confidence_tier':conf,'reasons':reasons or ['Conservative baseline blend.'],'warnings':warnings,'feature_breakdown':{'pitcher_safety_score':p,'offense_danger_score':o,'park_weather_score':pw,'certainty_score':c,'recent_form_score':r},'data_quality_score':c}
