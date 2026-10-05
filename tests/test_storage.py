"""Tests for the SQLite saved-jobs storage.

Each test gets its own empty database file in a temporary folder
(pytest's "tmp_path"), so tests never touch the real saved jobs.
"""

from datetime import date

import pytest

from backend.models import Job
from backend.storage import SavedJobsStore


@pytest.fixture
def store(tmp_path):
    return SavedJobsStore(tmp_path / "test.db")


def make_job(job_id="jobsuche:1", title="Barista"):
    return Job(
        id=job_id,
        source="jobsuche",
        title=title,
        company="Café Mühle",
        location="Berlin",
        distance_km=8,
        job_type="part_time",
        posted_date=date(2026, 10, 1),
        url="https://www.example.com/job/1",
    )


def test_new_store_is_empty(store):
    assert store.list_jobs() == []


def test_makes_the_data_folder(tmp_path):
    SavedJobsStore(tmp_path / "new_folder" / "jobs.db")
    assert (tmp_path / "new_folder" / "jobs.db").exists()


def test_save_and_list_a_job(store):
    saved = store.save_job(make_job())
    assert saved.status == "saved"
    assert saved.saved_at != ""

    jobs = store.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].title == "Barista"
    assert jobs[0].company == "Café Mühle"
    assert jobs[0].posted_date == date(2026, 10, 1)
    assert jobs[0].distance_km == 8


def test_saved_jobs_survive_a_restart(tmp_path):
    db_file = tmp_path / "jobs.db"
    SavedJobsStore(db_file).save_job(make_job())
    # A new store on the same file = the app was closed and opened again
    assert len(SavedJobsStore(db_file).list_jobs()) == 1


def test_saving_twice_keeps_one_copy_and_its_status(store):
    store.save_job(make_job())
    store.set_status("jobsuche:1", "applied")
    again = store.save_job(make_job())
    assert again.status == "applied"
    assert len(store.list_jobs()) == 1


def test_newest_saved_job_comes_first(store):
    store.save_job(make_job("jobsuche:1", "First"))
    store.save_job(make_job("jobsuche:2", "Second"))
    titles = []
    for job in store.list_jobs():
        titles.append(job.title)
    assert titles == ["Second", "First"]


def test_job_without_date_or_distance(store):
    job = make_job()
    job.posted_date = None
    job.distance_km = None
    saved = store.save_job(job)
    assert saved.posted_date is None
    assert saved.distance_km is None


def test_change_status(store):
    store.save_job(make_job())
    changed = store.set_status("jobsuche:1", "interview")
    assert changed.status == "interview"
    assert store.get_job("jobsuche:1").status == "interview"


def test_change_status_of_unknown_job_gives_none(store):
    assert store.set_status("jobsuche:nope", "applied") is None


def test_remove_job(store):
    store.save_job(make_job())
    assert store.remove_job("jobsuche:1") is True
    assert store.list_jobs() == []


def test_remove_unknown_job_gives_false(store):
    assert store.remove_job("jobsuche:nope") is False


def test_strange_characters_are_stored_safely(store):
    tricky_title = "Koch'; DROP TABLE saved_jobs; --"
    store.save_job(make_job(title=tricky_title))
    assert store.list_jobs()[0].title == tricky_title


def test_stats_when_empty(store):
    stats = store.stats()
    assert stats.saved == 0
    assert stats.applied == 0
    assert stats.replies == 0
    assert stats.interviews == 0


def test_stats_count_later_steps_too(store):
    statuses = ["saved", "saved", "applied", "replied", "interview", "rejected"]
    number = 0
    for status in statuses:
        number = number + 1
        job_id = f"jobsuche:{number}"
        store.save_job(make_job(job_id))
        store.set_status(job_id, status)

    stats = store.stats()
    assert stats.saved == 6        # every saved job
    assert stats.applied == 4      # applied, replied, interview, rejected
    assert stats.replies == 3      # replied, interview, rejected
    assert stats.interviews == 1
