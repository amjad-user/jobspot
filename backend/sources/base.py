"""The JobSource interface.

An "interface" is a promise: every job source class must have a "search"
method that takes SearchFilters and gives back a SearchResult.
The rest of the app only talks to this interface, so a new job source
(for example Adzuna) can be added later without changing the routes.
"""

from abc import ABC, abstractmethod

from backend.models import SearchFilters, SearchResult


class JobSourceError(Exception):
    """Something went wrong while asking a job source for jobs."""


class JobSourceUnavailable(JobSourceError):
    """The job source did not answer, or answered with an error."""


class PlaceNotFound(JobSourceError):
    """The job source does not know the place the person typed."""


class JobSource(ABC):
    """Base class for every job source."""

    # A short name, used in job ids (for example "jobsuche")
    name = "base"

    @abstractmethod
    def search(self, filters: SearchFilters) -> SearchResult:
        """Search for jobs. Must raise a JobSourceError if something fails."""
