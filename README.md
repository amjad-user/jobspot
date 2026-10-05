# JobSpot

A simple, friendly job search app. Type a job, pick a place, and see real job
listings from the Bundesagentur für Arbeit. Save jobs and track your progress.
You always apply on the employer's own page.

> Work in progress. The full README with screenshots comes at the end.

## Quick start (Windows)

Coming soon: double-click `start.bat`.

## For developers

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```
