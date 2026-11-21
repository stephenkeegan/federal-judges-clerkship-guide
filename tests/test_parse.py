from helper_functions import derive_party
from parse_oscar import first_last_key, normalize


def test_normalize():
    assert normalize("John P. Cronan") == "john cronan"

def test_first_last_key():
    assert first_last_key("John Peter Cronan") == "john cronan"

def test_derive_party():
    assert derive_party("Trump") == "Republican"
    assert derive_party("Biden") == "Democrat"
