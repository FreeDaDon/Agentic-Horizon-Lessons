from pager import page

ITEMS = list(range(25))


def test_first_page_starts_at_the_first_item():
    assert page(ITEMS, 1, 10) == list(range(0, 10))


def test_last_partial_page():
    assert page(ITEMS, 3, 10) == [20, 21, 22, 23, 24]


def test_page_past_the_end_is_empty():
    assert page(ITEMS, 4, 10) == []
