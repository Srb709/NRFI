from first_inning_lab.data_sources.mlb_stats_api import normalize_game

def test_normalize_game():
    g=normalize_game({'gamePk':1,'gameDate':'2026-04-29T01:00:00Z','teams':{'away':{'team':{'name':'A','id':1}},'home':{'team':{'name':'H','id':2}}},'venue':{'name':'V','id':3},'status':{'detailedState':'Scheduled'}})
    assert g['game_pk']==1 and g['away_team']=='A'
