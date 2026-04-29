from first_inning_lab.pipelines.build_today_board import run

def test_shape(monkeypatch):
    from first_inning_lab.pipelines import build_today_board as b
    monkeypatch.setattr(b,'get_schedule',lambda d:[{'game_id':'1','game_pk':1,'away_team':'A','home_team':'H','away_team_id':1,'home_team_id':2,'start_time':'','venue_id':None,'away_probable_pitcher_id':None,'home_probable_pitcher_id':None}])
    run('2026-04-29')
