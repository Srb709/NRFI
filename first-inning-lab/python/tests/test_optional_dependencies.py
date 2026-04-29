import importlib

from first_inning_lab.data_sources import pybaseball_client as pb


def test_mlb_stats_api_imports_without_requests():
    module = importlib.import_module('first_inning_lab.data_sources.mlb_stats_api')
    assert hasattr(module, 'get_schedule')


def test_pybaseball_client_safe_without_dep(monkeypatch):
    monkeypatch.setattr(pb, 'dependency_available', lambda _name: False)
    assert pb.get_pitching_stats_for_season(2026) == []
    assert pb.get_batting_stats_for_season(2026) == []
    assert pb.get_statcast_range('2026-04-01', '2026-04-10') == []
