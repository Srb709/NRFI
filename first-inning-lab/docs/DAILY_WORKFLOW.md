# DAILY_WORKFLOW

Run board build first, then launch dashboard.

- `python -m first_inning_lab.pipelines.build_today_board`
- `python -m first_inning_lab.pipelines.grade_first_innings`
- `npm run dev`

Admin page shows `LIVE LOCAL BOARD` when `data/live/today_board.json` is available, otherwise `DEMO MODE`.
Tracker shows `LIVE LOCAL RESULTS` from `data/live/today_results.json` / `data/live/public_record_updates.json`, else demo tracker fallback.
