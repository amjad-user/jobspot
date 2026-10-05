"""The JobSpot web server.

This file creates the FastAPI app. It has the API routes that the web page
calls, and it also serves the web page files from the "frontend" folder.

Every error the web page might show is a friendly sentence in "message",
never a technical error code.
"""

import logging
from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import config
from backend.models import SearchFilters, SearchResult
from backend.sources.base import JobSource, JobSourceUnavailable, PlaceNotFound
from backend.sources.jobsuche import JobsucheSource

logger = logging.getLogger("jobspot")

app = FastAPI(title="JobSpot")

# Friendly messages for the web page
MESSAGE_NO_PLACE = "Please tell us where you'd like to work, for example a town or a postcode."
MESSAGE_PLACE_NOT_FOUND = (
    "We couldn't find that place. Check the spelling, or try a nearby town or a postcode."
)
MESSAGE_SERVICE_DOWN = (
    "We can't reach the job listings right now. "
    "Please check your internet connection and try again in a minute."
)
MESSAGE_BAD_INPUT = "Something in your search doesn't look right. Please check it and try again."


class FriendlyError(Exception):
    """An error with a message that is safe and friendly to show on screen."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


@app.exception_handler(FriendlyError)
def handle_friendly_error(request: Request, error: FriendlyError):
    return JSONResponse(status_code=error.status_code, content={"message": error.message})


@app.exception_handler(RequestValidationError)
def handle_bad_input(request: Request, error: RequestValidationError):
    # FastAPI's normal answer here is very technical, so we replace it
    logger.info("Bad input: %s", error.errors())
    return JSONResponse(status_code=422, content={"message": MESSAGE_BAD_INPUT})


# ---------- job source ----------

# One job source for the whole app. It keeps one connection open, which is faster.
job_source = JobsucheSource()


def get_job_source() -> JobSource:
    """Gives the routes their job source. Tests replace this with a fake one."""
    return job_source


# ---------- routes ----------

@app.get("/api/health")
def health():
    """A tiny route to check that the server is running."""
    return {"status": "ok"}


@app.get("/api/jobs", response_model=SearchResult)
def search_jobs(
    where: str = "",
    what: str = "",
    distance: int = 25,
    job_type: str = "any",
    posted_days: Optional[int] = None,
    page: int = 1,
    source: JobSource = Depends(get_job_source),
):
    """Search for jobs.

    Example: /api/jobs?what=Barista&where=Berlin&distance=25&job_type=part_time&posted_days=7
    """
    where = where.strip()
    what = what.strip()
    if where == "":
        raise FriendlyError(400, MESSAGE_NO_PLACE)

    # Check the filters (Pydantic gives an error if a value is not allowed)
    try:
        filters = SearchFilters(
            what=what,
            where=where,
            distance_km=distance,
            job_type=job_type,
            posted_within_days=posted_days,
            page=page,
        )
    except ValueError as error:
        logger.info("Bad filters: %s", error)
        raise FriendlyError(422, MESSAGE_BAD_INPUT)

    # Ask the job source
    try:
        return source.search(filters)
    except PlaceNotFound:
        raise FriendlyError(404, MESSAGE_PLACE_NOT_FOUND)
    except JobSourceUnavailable as error:
        # The technical reason goes to the log, the friendly message to the screen
        logger.warning("Job source problem: %s", error)
        raise FriendlyError(503, MESSAGE_SERVICE_DOWN)


# Serve the web page. This must come last, so it does not hide the /api routes.
# html=True means "/" shows frontend/index.html.
app.mount("/", StaticFiles(directory=config.FRONTEND_DIR, html=True), name="frontend")
