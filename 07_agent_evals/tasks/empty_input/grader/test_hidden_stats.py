from stats import summarize


def test_empty_list():
    assert summarize([]) == {"count": 0, "min": None, "max": None, "mean": None}


def test_empty_generator():
    assert summarize(x for x in []) == {"count": 0, "min": None, "max": None, "mean": None}


def test_non_empty_unchanged():
    assert summarize([3, 1, 2]) == {"count": 3, "min": 1, "max": 3, "mean": 2.0}
