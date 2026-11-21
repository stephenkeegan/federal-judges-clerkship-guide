from courthouse_data import COURTHOUSE_COORDS, lookup_courthouse


def test_courthouse_known():
    # S.D.N.Y. Manhattan -> Thurgood Marshall Courthouse
    lat, lng, name = lookup_courthouse("Manhattan", "S.D.N.Y.")
    assert lat is not None
    assert "Thurgood Marshall" in name
    assert abs(lat - 40.7138) < 0.01


def test_courthouse_city_only_fallback():
    # Court abbreviation missing -> city-only lookup still resolves.
    lat, lng, name = lookup_courthouse("Manhattan", "")
    assert lat is not None
    assert "Thurgood Marshall" in name


def test_courthouse_missing():
    # Unknown duty station -> no match.
    assert lookup_courthouse("Nowhereville", "X.D. Fake") is None


def test_courthouse_table_nonempty():
    assert len(COURTHOUSE_COORDS) > 100