"""Job source: Bundesagentur für Arbeit "Jobsuche".

This file does two things:
1. It sends the search to the Bundesagentur job service (with httpx).
2. It turns their answer (German field names) into our own Job objects.

Field names were checked by hand on 2026-10-05 (see CLAUDE.md).
"""

from datetime import date
from typing import Optional
from urllib.parse import quote

import httpx

from backend import config
from backend.models import Job, SearchFilters, SearchResult
from backend.sources.base import JobSource, JobSourceUnavailable, PlaceNotFound

BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
SEARCH_PATH = "/pc/v6/jobs"
JOB_PAGE_URL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/"

# How many jobs we ask for per page
PAGE_SIZE = 24

# How long we wait for an answer, in seconds
TIMEOUT_SECONDS = 15


class JobsucheSource(JobSource):
    name = "jobsuche"

    def __init__(self, client: Optional[httpx.Client] = None):
        # Tests pass in their own client that gives fake answers.
        # In the real app we make a normal client.
        if client is None:
            client = httpx.Client(base_url=BASE_URL, timeout=TIMEOUT_SECONDS)
        self.client = client

    def search(self, filters: SearchFilters) -> SearchResult:
        params = build_params(filters)
        headers = {"X-API-Key": config.JOBSUCHE_API_KEY}

        # Step 1: ask the job service
        try:
            response = self.client.get(SEARCH_PATH, params=params, headers=headers)
        except httpx.HTTPError as error:
            # No internet, timeout, server not reachable, ...
            raise JobSourceUnavailable(f"Could not reach Jobsuche: {error}") from error

        if response.status_code != 200:
            raise JobSourceUnavailable(f"Jobsuche answered with status {response.status_code}")

        try:
            answer = response.json()
        except ValueError as error:
            raise JobSourceUnavailable("Jobsuche answer was not valid JSON") from error

        # Step 2: check if the place was understood
        where_info = answer.get("woOutput") or {}
        if where_info.get("suchmodus") == "UNGUELTIG":
            raise PlaceNotFound(f"Jobsuche does not know the place '{filters.where}'")

        # Step 3: turn every listing into our own Job shape
        # When there are no results, "ergebnisliste" is missing completely.
        raw_jobs = answer.get("ergebnisliste") or []
        jobs = []
        for raw_job in raw_jobs:
            job = convert_job(raw_job)
            if job is not None:
                jobs.append(job)

        # Newest jobs first (jobs without a date go to the end)
        jobs.sort(key=sort_key_newest_first)

        total = answer.get("maxErgebnisse") or 0
        place = where_info.get("bereinigterOrt") or filters.where
        has_more = filters.page * PAGE_SIZE < total

        return SearchResult(total=total, place=place, page=filters.page, has_more=has_more, jobs=jobs)


def build_params(filters: SearchFilters) -> dict:
    """Turn our filters into the German parameter names the service expects."""
    params = {
        "wo": filters.where,
        "umkreis": filters.distance_km,
        "page": filters.page,
        "size": PAGE_SIZE,
    }
    if filters.what:
        params["was"] = filters.what

    if filters.job_type == "full_time":
        params["arbeitszeit"] = "vz"    # vz = Vollzeit = full-time
    elif filters.job_type == "part_time":
        params["arbeitszeit"] = "tz"    # tz = Teilzeit = part-time

    if filters.posted_within_days is not None:
        params["veroeffentlichtseit"] = filters.posted_within_days

    return params


def convert_job(raw: dict) -> Optional[Job]:
    """Turn one Jobsuche listing into our Job shape.

    Returns None if the listing is missing the things we really need
    (an id and a title), so one broken listing does not break the search.
    """
    ref_number = raw.get("referenznummer")
    title = raw.get("stellenangebotsTitel")
    if not ref_number or not title:
        return None

    return Job(
        id=f"jobsuche:{ref_number}",
        source="jobsuche",
        title=title.strip(),
        company=(raw.get("firma") or "").strip(),
        location=read_location(raw),
        distance_km=raw.get("entfernung"),
        job_type=read_job_type(raw),
        posted_date=read_posted_date(raw),
        url=read_url(raw, ref_number),
    )


def read_location(raw: dict) -> str:
    """The town of the first work place, for example "Berlin"."""
    places = raw.get("stellenlokationen") or []
    if len(places) == 0:
        return ""
    address = places[0].get("adresse") or {}
    town = address.get("ort")
    if town:
        return town
    region = address.get("region")
    if region:
        # Regions come in capitals ("BERLIN"), so make them look nicer
        return region.title()
    return ""


def read_job_type(raw: dict) -> str:
    """Full-time, part-time, both, or not stated."""
    is_full_time = raw.get("arbeitszeitVollzeit") is True

    # Part-time is split into several fields (morning, afternoon, evening, ...)
    is_part_time = False
    for field_name in raw:
        if field_name.startswith("arbeitszeitTeilzeit") and raw[field_name] is True:
            is_part_time = True

    if is_full_time and is_part_time:
        return "full_or_part_time"
    if is_full_time:
        return "full_time"
    if is_part_time:
        return "part_time"
    return "not_stated"


def read_posted_date(raw: dict) -> Optional[date]:
    """The date the job was (last) published."""
    period = raw.get("veroeffentlichungszeitraum") or {}
    date_text = period.get("von") or raw.get("datumErsteVeroeffentlichung")
    if not date_text:
        return None
    try:
        return date.fromisoformat(date_text[:10])
    except ValueError:
        return None


def read_url(raw: dict, ref_number: str) -> str:
    """Link to the original job page.

    We use the employer's own link if there is one, but only if it is a
    normal web link (http or https), for safety. Otherwise we link to the
    job's page on arbeitsagentur.de.
    """
    external_url = raw.get("externeURL") or ""
    if external_url.startswith("https://") or external_url.startswith("http://"):
        return external_url
    # quote() makes the id safe to put inside a web address
    return JOB_PAGE_URL + quote(ref_number)


def sort_key_newest_first(job: Job):
    """Used by sort(): newest date first, jobs without a date last."""
    if job.posted_date is None:
        return (1, 0)
    # A bigger date number means newer, so we use minus to put it first
    return (0, -job.posted_date.toordinal())
