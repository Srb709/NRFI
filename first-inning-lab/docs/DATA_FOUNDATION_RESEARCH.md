# Data Foundation Research

## Smoke-test date
- 2026-04-29 (UTC).

## MLB Stats API endpoints tested
- `/api/v1/schedule?sportId=1&date=2026-04-29&hydrate=probablePitcher,venue`
- `/api/v1/game/{gamePk}/feed/live`
- `/api/v1/game/{gamePk}/boxscore`
- `/api/v1/game/{gamePk}/linescore`
- `/api/v1/people/{personId}/stats?stats=season&group=pitching&season=2026`
- `/api/v1/stats?stats=season&group=hitting&teamId={teamId}&season=2026`
- `/api/v1/teams?sportId=1&hydrate=venue(location,timezone)`

## Open-Meteo endpoint tested
- `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,wind_speed_10m,wind_direction_10m&timezone=UTC`

## Response shape notes
- `schedule` includes gamePk, gameDate, teams.away/home.team.id/name, probablePitcher, venue.id/name.
- `feed/live` contains `liveData.boxscore.teams.{away,home}.players` with optional `battingOrder`.
- `boxscore` endpoint has similar teams/players structure and is a viable fallback.
- `linescore.innings[0].away.runs` and `home.runs` can derive FI outcomes.
- player/team season stat endpoints expose split-based `stat` objects.

## Available fields
- Schedule venue/team IDs, probable pitchers.
- Pitcher ERA/WHIP style season stats.
- Team offense OBP/SLG/OPS/runs.
- Lineup batting order when posted.
- First inning runs from linescore for completed games.

## Not reliably available
- Confirmed batting order for early games.
- Park factor values from MLB Stats API.
- Sometimes weather request access (network/proxy dependent).

## Locally derived data
- Park/weather feature score composition.
- Pricing readiness classification.
- Historical FI rates by team/pitcher/venue (sample-size gated).

## Future work
- Verified park factors from internal historical derivation.
- Stronger wind-direction park interaction.
- Expanded lineup quality model beyond top-4 hitters.
