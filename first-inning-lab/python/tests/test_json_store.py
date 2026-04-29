from first_inning_lab.storage.json_store import *
def test_read_default(tmp_path):
    assert read_json(tmp_path/'x.json',default=[])==[]
