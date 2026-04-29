import json, os, tempfile
from pathlib import Path

def ensure_parent_dir(path): Path(path).parent.mkdir(parents=True, exist_ok=True)
def read_json(path, default=None):
    try:
        with open(path,'r',encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError: return default
    except Exception: return default

def write_json(path, data):
    ensure_parent_dir(path)
    with open(path,'w',encoding='utf-8') as f: json.dump(data,f,indent=2)

def atomic_write_json(path, data):
    ensure_parent_dir(path)
    d=Path(path).parent
    with tempfile.NamedTemporaryFile('w',delete=False,dir=d,encoding='utf-8') as t:
        json.dump(data,t,indent=2); tmp=t.name
    os.replace(tmp,path)
