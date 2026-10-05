"""Helpers that let tests use fake job-service answers instead of the internet."""

import json
from pathlib import Path

import httpx

from backend.sources.jobsuche import BASE_URL, JobsucheSource

FAKE_ANSWERS_DIR = Path(__file__).parent / "fake_answers"


def load_fake_answer(file_name: str) -> dict:
    """Read one of the saved fake answers from tests/fake_answers/."""
    path = FAKE_ANSWERS_DIR / file_name
    with open(path, encoding="utf-8") as file:
        return json.load(file)


class FakeJobService:
    """Pretends to be the Bundesagentur job service.

    It remembers every request it gets (so tests can check the parameters)
    and answers with whatever the test asked for.
    """

    def __init__(self, answer=None, status_code=200, fail_with=None):
        self.answer = answer
        self.status_code = status_code
        self.fail_with = fail_with      # an error to raise, for example a timeout
        self.requests = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.fail_with is not None:
            raise self.fail_with
        return httpx.Response(self.status_code, json=self.answer)

    def make_source(self) -> JobsucheSource:
        """A JobsucheSource that talks to this fake service."""
        transport = httpx.MockTransport(self.handle)
        client = httpx.Client(base_url=BASE_URL, transport=transport)
        return JobsucheSource(client=client)
