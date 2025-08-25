from scripts.ckan_migrate.helpers import ensure_unique_name


def test_ensure_unique_name_when_free():
    assert ensure_unique_name("foo", lambda n: False) == "foo"


def test_ensure_unique_name_when_taken_adds_suffix():
    taken = {"foo", "foo-0001"}
    assert ensure_unique_name("foo", lambda n: n in taken, suffix_seed="0001").startswith("foo-")
