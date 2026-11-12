def page(items, page_number, page_size):
    """Return the items on a 1-indexed page."""
    start = page_number * page_size
    return items[start:start + page_size]
