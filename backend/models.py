"""Data shapes used everywhere in JobSpot.

Every job source (for example the Bundesagentur) gives us jobs in its own
format. We turn them into our own simple "Job" shape, so the rest of the
app (and the web page) only ever has to understand one format.

Pydantic checks the data for us: if a field has the wrong type, it raises
an error instead of letting bad data into the app.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# The kinds of working time a job can have
JobType = Literal["full_time", "part_time", "full_or_part_time", "not_stated"]


class Job(BaseModel):
    """One job listing, in our own simple shape."""

    id: str                         # unique id, for example "jobsuche:10001-123-S"
    source: str                     # which job source it came from, for example "jobsuche"
    title: str
    company: str                    # empty text if the listing does not name a company
    location: str                   # for example "Berlin"
    distance_km: Optional[int] = None   # distance from the searched place
    job_type: JobType = "not_stated"
    posted_date: Optional[date] = None
    url: str                        # the original job page, where the person applies

    @field_validator("url")
    @classmethod
    def url_must_be_a_web_link(cls, url: str) -> str:
        """Only allow normal web links, so a bad link can never run code in the page."""
        if url.startswith("https://") or url.startswith("http://"):
            return url
        raise ValueError("url must start with http:// or https://")


class SearchFilters(BaseModel):
    """What the person is searching for."""

    what: str = ""                  # the job, for example "Barista"
    where: str                      # the place, for example "Berlin"
    distance_km: int = Field(default=25, ge=0, le=200)
    job_type: Literal["any", "part_time", "full_time"] = "any"
    posted_within_days: Optional[int] = Field(default=None, ge=0, le=100)
    page: int = Field(default=1, ge=1, le=40)


# The steps of applying for a saved job
JobStatus = Literal["saved", "applied", "replied", "interview", "rejected"]


class SavedJob(Job):
    """A job the person saved. It has everything a Job has, plus progress."""

    status: JobStatus = "saved"
    saved_at: str = ""              # date and time it was saved, for example "2026-10-05T14:30:00"


class StatusChange(BaseModel):
    """What the web page sends to change the status of a saved job."""

    status: JobStatus


class Stats(BaseModel):
    """Simple numbers for the saved jobs page."""

    saved: int          # all saved jobs
    applied: int        # jobs the person applied to (applied, got a reply, interview or rejected)
    replies: int        # jobs where the employer answered (got a reply, interview or rejected)
    interviews: int     # jobs with an interview


class SearchResult(BaseModel):
    """The answer to one search."""

    total: int                      # how many jobs match in total (all pages)
    place: str                      # the place name, cleaned up by the job source
    page: int
    has_more: bool                  # True if there is another page of jobs
    jobs: list[Job]
