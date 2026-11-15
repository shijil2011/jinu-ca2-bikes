# Dublin Bikes collector

This repo collects live Dublin Bikes data for an MSc continuous assessment (B9AI001).

## Source

Station status comes from the official JCDecaux Dublin Bikes GBFS v3 feed. The feed does not need an API key, and it is listed on [data.smartdublin.ie](https://data.smartdublin.ie/). Each snapshot also stores the current weather for central Dublin from Open-Meteo (temperature, humidity, wind speed, precipitation, and weather code).

## Schedule

GitHub Actions runs `collectors/bikes_collect.py` every 15 minutes (`*/15 * * * *`). You can also start a run from the Actions tab with **Run workflow**. GitHub cron can be delayed or skipped.

## Files

- Daily snapshots: `data/bikes/csv/<YYYY-MM-DD>.csv` (one file per day; each run appends one row per station)
- Station list, written once: `data/bikes/stations.csv`
- Run log: `logs/bikes_collection_log.csv`

SQLite is rebuilt from these CSVs later. Never commit `.db` files. They are ignored by git.

## Run it manually

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-collect.txt
python collectors/bikes_collect.py
```

On Windows, `bats/run_bikes.bat` is a Task Scheduler fallback. Edit the `cd /d` line so it points at this repo, create the virtual environment, then schedule the batch file.

Set `BIKES_USER_AGENT` if you want a contact string in the request header. The GitHub Action reads the repository variable of the same name. If it is empty, the script uses a default student-project user agent.
