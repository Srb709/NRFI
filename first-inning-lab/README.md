# First Inning Lab

Local NRFI/YRFI model board and tracker dashboard.

## Local workflow
1. Pull latest code:
```bash
git pull
```
2. Python setup:
```bash
cd first-inning-lab/python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
3. Build today's board:
```bash
python -m first_inning_lab.pipelines.build_today_board
```
4. Grade first innings:
```bash
python -m first_inning_lab.pipelines.grade_first_innings
```
5. Start dashboard:
```bash
cd ..
npm run dev
```
6. Open:
- http://localhost:3000/admin
- http://localhost:3000/tracker

Dashboard reads live local files first, then falls back to demo mode if live files are missing. Early board is not final board; missing data lowers confidence, and PASS is a valid output. No paid APIs or sportsbook scraping are used.
