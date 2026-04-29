# First Inning Lab
Model-based first-inning baseball analytics demo dashboard.

## What this is
A local demo for NRFI/YRFI board generation, risk notes, content drafting, and public record tracking.

## What this is not
Not betting advice, not guaranteed outcomes, no auto-posting, and no bet placement.

## Local setup
```bash
cd first-inning-lab
npm install
npm run dev
```
Open:
- http://localhost:3000
- http://localhost:3000/admin
- http://localhost:3000/tracker

## Python
```bash
cd first-inning-lab/python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
```

## Troubleshooting
If demo JSON files fail to load, server falls back to bundled demo imports.

## Current limitations
Demo-only data, no live MLB ingestion, simple baseline model.

## Next steps
Live data ingestion, historical backtests, scheduled jobs, and auth.

## Free local data engine
Use python pipelines under `python/first_inning_lab/pipelines`.
