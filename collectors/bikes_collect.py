"""Save one snapshot of Dublin Bikes station status (no API key).

Official GBFS v3 feed, also listed on data.smartdublin.ie.
Run:  python collectors/bikes_collect.py
"""
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.cyclocity.fr/contracts/dublin/gbfs/v3"
STATUS_URL = f"{BASE}/station_status.json"
INFO_URL = f"{BASE}/station_information.json"
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast?latitude=53.3498&longitude=-6.2603"
    "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code"
)
ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = Path(os.environ.get("BIKES_CSV_DIR", ROOT / "data" / "bikes" / "csv"))
STATIONS_PATH = Path(os.environ.get("BIKES_STATIONS_PATH", ROOT / "data" / "bikes" / "stations.csv"))
LOG_PATH = Path(os.environ.get("BIKES_LOG_PATH", ROOT / "logs" / "bikes_collection_log.csv"))
STATE_FILE = Path(os.environ.get("BIKES_STATE_FILE", ROOT / "data" / "bikes" / "last_updated.txt"))
USER_AGENT = os.environ.get("BIKES_USER_AGENT") or "jinu-ca2-bikes/1.0 (DBS MSc student project)"

COLUMNS = [
    "collected_at", "feed_last_updated", "station_id",
    "num_bikes", "mechanical", "electrical",
    "num_bikes_disabled", "num_docks_available", "num_docks_disabled",
    "is_installed", "is_renting", "is_returning", "last_reported",
    "temperature", "humidity", "wind_speed", "precipitation", "weather_code",
]


def get_json(url):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def save_stations_once():
    if STATIONS_PATH.exists():
        return
    info = get_json(INFO_URL)
    STATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATIONS_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["station_id", "name", "address", "lat", "lon", "capacity"])
        for s in info["data"]["stations"]:
            name = s["name"]
            if isinstance(name, list):
                name = name[0].get("text", "") if name else ""
            w.writerow([s["station_id"], name, s.get("address", ""),
                        s["lat"], s["lon"], s.get("capacity", "")])


def write_log(entry):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = ["run_at_utc", "status", "http_status", "stations", "rows_new", "skipped", "error"]
    new_file = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        w.writerow({k: entry.get(k, "") for k in fields})


def run_once():
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {"run_at_utc": collected_at, "status": "error", "skipped": 0, "rows_new": 0}
    try:
        save_stations_once()
        status = get_json(STATUS_URL)
        feed_time = str(status.get("last_updated"))
        if STATE_FILE.exists() and STATE_FILE.read_text(encoding="utf-8").strip() == feed_time:
            entry.update(status="ok", skipped=1, stations=len(status.get("data", {}).get("stations") or []))
            write_log(entry)
            return entry
        try:
    weather_response = get_json(
        WEATHER_URL,
        retries=3,
        timeout=15
    )

    weather = weather_response.get("current")

    if not weather:
        raise ValueError("Weather API returned no current data")

    logging.info(
        "Weather fetched successfully: temperature=%s, humidity=%s",
        weather.get("temperature_2m"),
        weather.get("relative_humidity_2m")
    )

except (requests.RequestException, ValueError) as exc:
    logging.error(
        "Weather unavailable after retries: %s",
        exc
    )
    weather = {}
        rows = []
        for s in status["data"]["stations"]:
            types = {t["vehicle_type_id"]: t["count"] for t in s.get("vehicle_types_available", [])}
            rows.append({
                "collected_at": collected_at,
                "feed_last_updated": feed_time,
                "station_id": s["station_id"],
                "num_bikes": s.get("num_vehicles_available"),
                "mechanical": types.get("mechanical", 0),
                "electrical": types.get("electrical", 0),
                "num_bikes_disabled": s.get("num_vehicles_disabled", 0),
                "num_docks_available": s.get("num_docks_available"),
                "num_docks_disabled": s.get("num_docks_disabled", 0),
                "is_installed": s.get("is_installed"),
                "is_renting": s.get("is_renting"),
                "is_returning": s.get("is_returning"),
                "last_reported": s.get("last_reported"),
                "temperature": weather.get("temperature_2m"),
                "humidity": weather.get("relative_humidity_2m"),
                "wind_speed": weather.get("wind_speed_10m"),
                "precipitation": weather.get("precipitation"),
                "weather_code": weather.get("weather_code"),
            })
        out = CSV_DIR / f"{collected_at[:10]}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        new_file = not out.exists()
        with out.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            if new_file:
                w.writeheader()
            w.writerows(rows)
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(feed_time, encoding="utf-8")
        entry.update(status="ok", http_status=200, stations=len(rows), rows_new=len(rows), skipped=0)
    except Exception as exc:
        entry["error"] = f"{type(exc).__name__}: {exc}"[:300]
    write_log(entry)
    return entry


if __name__ == "__main__":
    print(run_once())
