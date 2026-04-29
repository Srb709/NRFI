from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def today_et()->str: return datetime.now(ZoneInfo('America/New_York')).date().isoformat()
def parse_date(s:str): return datetime.strptime(s,'%Y-%m-%d').date()
def date_range(start,end):
    cur=parse_date(start); e=parse_date(end)
    while cur<=e:
        yield cur.isoformat(); cur += timedelta(days=1)
