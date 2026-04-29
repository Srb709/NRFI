BANNED = ['guaranteed winner','lock','max bet','hammer','mortgage','free money','can’t lose','cant lose','risk-free','risk free','sure thing']

def _sanitize(text: str) -> str:
    out = text
    for p in BANNED:
        out = out.replace(p, 'high-confidence angle').replace(p.title(), 'High-confidence angle')
    return out

def _safe(text: str) -> str:
    s = _sanitize(text)
    if any(p in s.lower() for p in BANNED):
        return 'Content held for review. No guarantees. Just the board.'
    return s

def generate_posts(board: list[dict]) -> dict:
    lines = [f"- {r['game']}: {r['public_label']} ({r['lean']})" for r in board[:10]]
    return {
        'dailyBoard': _safe('Daily board\n' + '\n'.join(lines) + '\nNo guarantees. Just the board.'),
        'cleanSetupPost': _safe('Clean setup watch\nReview clean first-inning setup spots.'),
        'yrfiSmokePost': _safe('YRFI smoke watch\nMonitor top-of-order danger and early traffic risk.'),
        'trapWatchPost': _safe('Trap watch\nFlag chaos zone and pass spot games.'),
        'resultsRecapTemplate': _safe('Results recap\nNRFI [W-L]\nYRFI [W-L]\nNotes: [context]'),
        'discord': _safe('Early Discord board\n' + '\n'.join(lines[:6]))
    }
