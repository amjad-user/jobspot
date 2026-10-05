"""Saved jobs storage, using SQLite.

SQLite keeps a whole database in one normal file on this computer
(by default data/jobspot.db). Nothing is sent anywhere.

We open a new connection for every action and close it again. That is
simple, and it is safe when the web server handles several requests at once.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.models import Job, SavedJob, Stats

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS saved_jobs (
    id          TEXT PRIMARY KEY,
    source      TEXT NOT NULL,
    title       TEXT NOT NULL,
    company     TEXT NOT NULL,
    location    TEXT NOT NULL,
    distance_km INTEGER,
    job_type    TEXT NOT NULL,
    posted_date TEXT,
    url         TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'saved',
    saved_at    TEXT NOT NULL
)
"""


class SavedJobsStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        # Make the "data" folder if it does not exist yet
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = self._connect()
        try:
            connection.execute(CREATE_TABLE_SQL)
            connection.commit()
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        # Lets us read columns by name, like row["title"]
        connection.row_factory = sqlite3.Row
        return connection

    def list_jobs(self) -> list[SavedJob]:
        """All saved jobs, the most recently saved first."""
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM saved_jobs ORDER BY saved_at DESC, rowid DESC"
            ).fetchall()
        finally:
            connection.close()

        saved_jobs = []
        for row in rows:
            saved_jobs.append(row_to_saved_job(row))
        return saved_jobs

    def get_job(self, job_id: str) -> Optional[SavedJob]:
        """One saved job, or None if it is not saved."""
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM saved_jobs WHERE id = ?", (job_id,)
            ).fetchone()
        finally:
            connection.close()

        if row is None:
            return None
        return row_to_saved_job(row)

    def save_job(self, job: Job) -> SavedJob:
        """Save a job. If it is already saved, keep it as it is (and keep its status)."""
        already_saved = self.get_job(job.id)
        if already_saved is not None:
            return already_saved

        posted_date_text = None
        if job.posted_date is not None:
            posted_date_text = job.posted_date.isoformat()
        saved_at = datetime.now().isoformat(timespec="seconds")

        connection = self._connect()
        try:
            # The "?" marks are filled in by SQLite itself. This keeps the
            # database safe, even if a job title contains strange characters.
            connection.execute(
                """
                INSERT INTO saved_jobs
                    (id, source, title, company, location, distance_km,
                     job_type, posted_date, url, status, saved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'saved', ?)
                """,
                (
                    job.id, job.source, job.title, job.company, job.location,
                    job.distance_km, job.job_type, posted_date_text, job.url, saved_at,
                ),
            )
            connection.commit()
        finally:
            connection.close()

        return self.get_job(job.id)

    def set_status(self, job_id: str, status: str) -> Optional[SavedJob]:
        """Change the status of a saved job. Returns None if the job is not saved."""
        connection = self._connect()
        try:
            cursor = connection.execute(
                "UPDATE saved_jobs SET status = ? WHERE id = ?", (status, job_id)
            )
            connection.commit()
            changed_rows = cursor.rowcount
        finally:
            connection.close()

        if changed_rows == 0:
            return None
        return self.get_job(job_id)

    def remove_job(self, job_id: str) -> bool:
        """Remove a saved job. Returns False if it was not saved."""
        connection = self._connect()
        try:
            cursor = connection.execute("DELETE FROM saved_jobs WHERE id = ?", (job_id,))
            connection.commit()
            removed_rows = cursor.rowcount
        finally:
            connection.close()

        return removed_rows > 0

    def stats(self) -> Stats:
        """Count the saved jobs by how far the person got."""
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT status, COUNT(*) AS how_many FROM saved_jobs GROUP BY status"
            ).fetchall()
        finally:
            connection.close()

        # How many jobs have each status, for example {"saved": 3, "applied": 1}
        count_by_status = {}
        for row in rows:
            count_by_status[row["status"]] = row["how_many"]

        saved = count_by_status.get("saved", 0)
        applied = count_by_status.get("applied", 0)
        replied = count_by_status.get("replied", 0)
        interview = count_by_status.get("interview", 0)
        rejected = count_by_status.get("rejected", 0)

        # A job with an interview was also applied to and got a reply,
        # so the later steps also count for the earlier numbers.
        return Stats(
            saved=saved + applied + replied + interview + rejected,
            applied=applied + replied + interview + rejected,
            replies=replied + interview + rejected,
            interviews=interview,
        )


def row_to_saved_job(row: sqlite3.Row) -> SavedJob:
    """Turn one database row into a SavedJob."""
    return SavedJob(
        id=row["id"],
        source=row["source"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        distance_km=row["distance_km"],
        job_type=row["job_type"],
        posted_date=row["posted_date"],
        url=row["url"],
        status=row["status"],
        saved_at=row["saved_at"],
    )
