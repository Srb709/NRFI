from typing import Dict,Any

def map_public_label(nrfi,yrfi,warning_count):
    if nrfi>=0.64 and warning_count<=1:return 'Lab Favorite'
    if nrfi>=0.59:return 'Clean First Frame'
    if nrfi>=0.55:return 'Quiet Inning Candidate'
    if yrfi>=0.59:return 'YRFI Smoke'
    if yrfi>=0.55:return 'Chaos Zone'
    return 'Pass'

def predict_game(features:Dict[str,Any]):
    p=0.5; reasons=[]; warnings=[]
    if features.get('season_bb_rate',0.08)<0.08: p+=0.04; reasons.append('Both starters suppress walks')
    if features.get('season_k_rate',0.22)>0.23: p+=0.03; reasons.append('Strikeout ability limits early traffic')
    if features.get('projected_top_3_obp',0.33)>0.34: p-=0.04; reasons.append('Top-of-order danger present')
    if features.get('weather_run_boost',0)>0.1: p-=0.03; warnings.append('Weather adds run environment')
    if features.get('unconfirmed_lineups',True): warnings.append('Lineups unconfirmed')
    p=max(0.35,min(0.70,p)); y=1-p
    lean='NRFI' if p>=0.55 else ('YRFI' if y>=0.55 else 'PASS')
    return {'nrfi_probability':round(p,3),'yrfi_probability':round(y,3),'lean':lean,'public_label':map_public_label(p,y,len(warnings)),'reasons':reasons,'warnings':warnings}
