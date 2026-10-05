"""Tests for the Bundesagentur Jobsuche client (no internet needed)."""

from datetime import date

import httpx
import pytest

from backend.models import SearchFilters
from backend.sources.base import JobSourceUnavailable, PlaceNotFound
from tests.fakes import FakeJobService, load_fake_answer


def search_with(answer, **filter_values):
    """Run one search against a fake service. Returns (result, fake_service)."""
    fake = FakeJobService(answer=answer)
    source = fake.make_source()
    if "where" not in filter_values:
        filter_values["where"] = "Berlin"
    result = source.search(SearchFilters(**filter_values))
    return result, fake


def find_job(jobs, title_start):
    """Find the first job whose title starts with the given text."""
    for job in jobs:
        if job.title.startswith(title_start):
            return job
    return None


# ---------- turning the answer into Job objects ----------

def test_converts_all_listings_into_jobs():
    result, _ = search_with(load_fake_answer("jobsuche_search.json"), what="Barista")
    assert len(result.jobs) == 4
    assert result.total == 6
    assert result.place == "Berlin"


def test_job_fields_are_filled_in():
    result, _ = search_with(load_fake_answer("jobsuche_search.json"))
    job = find_job(result.jobs, "Barista in Teilzeit (m/w/d)")
    assert job.id == "jobsuche:13635-4f50abb5_JB5264739-S"
    assert job.source == "jobsuche"
    assert job.company == "Kaffeebar Sonnenschein GmbH"
    assert job.location == "Berlin"
    assert job.distance_km == 8
    assert job.posted_date == date(2026, 9, 30)


def test_german_letters_stay_correct():
    result, _ = search_with(load_fake_answer("jobsuche_search.json"))
    companies = []
    for job in result.jobs:
        companies.append(job.company)
    assert "Café Mühle & Söhne" in companies


def test_job_types():
    result, _ = search_with(load_fake_answer("jobsuche_search.json"))
    types = {}
    for job in result.jobs:
        types[job.title] = job.job_type
    assert types["Barista in Teilzeit (m/w/d)"] == "part_time"
    assert types["Barista ( m/w/d)"] == "full_or_part_time"
    assert types["News Cafe Barista (m/f/d)"] == "not_stated"
    assert types["Mitarbeiter Gästebetreuung & Barista (m/w/x)"] == "full_time"


def test_uses_external_link_when_there_is_one():
    result, _ = search_with(load_fake_answer("jobsuche_search.json"))
    job = find_job(result.jobs, "Barista in Teilzeit (m/w/d)")
    assert job.url == "https://www.example.com/jobs/barista-123"


def test_uses_arbeitsagentur_link_when_there_is_no_external_link():
    result, _ = search_with(load_fake_answer("jobsuche_search.json"))
    job = find_job(result.jobs, "Barista ( m/w/d)")
    assert job.url == "https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1003416537-S"


def test_ignores_unsafe_links():
    answer = load_fake_answer("jobsuche_search.json")
    answer["ergebnisliste"][0]["externeURL"] = "javascript:alert(1)"
    result, _ = search_with(answer)
    for job in result.jobs:
        assert not job.url.startswith("javascript")


def test_missing_company_and_location_become_empty_text():
    result, _ = search_with(load_fake_answer("jobsuche_search.json"))
    no_company = find_job(result.jobs, "News Cafe Barista (m/f/d)")
    assert no_company.company == ""
    no_location = find_job(result.jobs, "Mitarbeiter")
    assert no_location.location == ""
    assert no_location.distance_km is None


def test_skips_broken_listings():
    answer = load_fake_answer("jobsuche_search.json")
    answer["ergebnisliste"].append({"stellenangebotsTitel": "No id here"})
    result, _ = search_with(answer)
    assert len(result.jobs) == 4


def test_newest_jobs_come_first():
    result, _ = search_with(load_fake_answer("jobsuche_search.json"))
    dates = []
    for job in result.jobs:
        dates.append(job.posted_date)
    assert dates == [date(2026, 10, 5), date(2026, 9, 30), date(2026, 9, 16), date(2026, 7, 21)]


def test_no_results_gives_empty_list():
    # When there are no results, the service leaves out "ergebnisliste" completely
    result, _ = search_with(load_fake_answer("jobsuche_no_results.json"), what="xyz")
    assert result.jobs == []
    assert result.total == 0
    assert result.has_more is False


def test_has_more_pages():
    answer = load_fake_answer("jobsuche_search.json")
    answer["maxErgebnisse"] = 100
    result, _ = search_with(answer)
    assert result.has_more is True


# ---------- the request we send ----------

def test_sends_api_key_and_search_words():
    _, fake = search_with(load_fake_answer("jobsuche_search.json"), what="Barista", where="Berlin")
    request = fake.requests[0]
    assert request.url.path.endswith("/pc/v6/jobs")
    assert request.headers["X-API-Key"] == "jobboerse-jobsuche"
    assert request.url.params["was"] == "Barista"
    assert request.url.params["wo"] == "Berlin"
    assert request.url.params["umkreis"] == "25"
    assert request.url.params["page"] == "1"


def test_sends_filters():
    _, fake = search_with(
        load_fake_answer("jobsuche_search.json"),
        what="Barista", distance_km=50, job_type="part_time", posted_within_days=7, page=2,
    )
    params = fake.requests[0].url.params
    assert params["umkreis"] == "50"
    assert params["arbeitszeit"] == "tz"
    assert params["veroeffentlichtseit"] == "7"
    assert params["page"] == "2"


def test_full_time_filter():
    _, fake = search_with(load_fake_answer("jobsuche_search.json"), job_type="full_time")
    assert fake.requests[0].url.params["arbeitszeit"] == "vz"


def test_no_job_type_or_date_filter_by_default():
    _, fake = search_with(load_fake_answer("jobsuche_search.json"))
    params = fake.requests[0].url.params
    assert "arbeitszeit" not in params
    assert "veroeffentlichtseit" not in params
    assert "was" not in params


# ---------- when things go wrong ----------

def test_unknown_place_raises_place_not_found():
    with pytest.raises(PlaceNotFound):
        search_with(load_fake_answer("jobsuche_unknown_place.json"), where="Xqzv")


def test_server_error_raises_unavailable():
    fake = FakeJobService(answer={"error": "oops"}, status_code=500)
    with pytest.raises(JobSourceUnavailable):
        fake.make_source().search(SearchFilters(where="Berlin"))


def test_forbidden_raises_unavailable():
    fake = FakeJobService(answer={}, status_code=403)
    with pytest.raises(JobSourceUnavailable):
        fake.make_source().search(SearchFilters(where="Berlin"))


def test_timeout_raises_unavailable():
    fake = FakeJobService(fail_with=httpx.ReadTimeout("too slow"))
    with pytest.raises(JobSourceUnavailable):
        fake.make_source().search(SearchFilters(where="Berlin"))


def test_no_internet_raises_unavailable():
    fake = FakeJobService(fail_with=httpx.ConnectError("no internet"))
    with pytest.raises(JobSourceUnavailable):
        fake.make_source().search(SearchFilters(where="Berlin"))
