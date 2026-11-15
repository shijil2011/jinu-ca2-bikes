@echo off
REM Windows Task Scheduler fallback for Dublin Bikes collection.
REM Replace the path below with the folder that contains this repo.
cd /d C:\path\to\jinu-ca2-bikes
call .venv\Scripts\activate
python collectors\bikes_collect.py
