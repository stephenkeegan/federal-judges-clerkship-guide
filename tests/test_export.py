from export_site_data import _clean, _court_from_summary, _parse_year, _years_of_service
from helper_functions import derive_party
from parse_oscar import first_last_key, normalize


def test_clean():
    assert _clean(None) is None
    assert _clean(float("nan")) is None
    assert _clean("  ") is None
    assert _clean("nan") is None
    assert _clean("hello") == "hello"


def test_parse_year():
    assert _parse_year("born 1981") == 1981
    assert _parse_year("1981.0") == 1981
    assert _parse_year(None) is None
    assert _parse_year("no year here") is None


def test_court_from_summary():
    s = "Adam Ben Abelson is a United States district judge of the United States District Court for the District of Maryland."
    assert _court_from_summary(s) == "United States District Court for the District of Maryland"
    assert _court_from_summary(None) is None
    # Falls back to generic court type if district not parseable
    s2 = "Allyne Ronna Ross is a senior United States district judge of the United States District Court."
    assert "United States District Court" in _court_from_summary(s2)


def test_years_of_service():
    row = {"Began active service": "2012 present"}
    assert _years_of_service(row, 2026) == 14
    assert _years_of_service({}, 2026) is None


def test_normalize():
    assert normalize("John P. Cronan") == "john cronan"


def test_first_last_key():
    assert first_last_key("John Peter Cronan") == "john cronan"


def test_derive_party():
    assert derive_party("Trump") == "Republican"
    assert derive_party("Biden") == "Democrat"