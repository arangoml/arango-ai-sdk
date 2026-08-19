import arango_ai


def test_version_is_exposed() -> None:
    assert arango_ai.__version__
