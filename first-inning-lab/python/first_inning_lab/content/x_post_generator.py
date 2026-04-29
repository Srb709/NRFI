BANNED=['guaranteed','max bet','mortgage','free money','can’t lose','hammer','risk-free']

def generate_daily_board(games):
    txt="Today's First Inning Lab board:\n\nNo locks. Just the board."
    low=txt.lower()
    assert not any(b in low for b in BANNED)
    return txt
