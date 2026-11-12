FREE_SHIPPING_THRESHOLD = 100.00
FLAT_FEE = 5.00


def shipping_cost(total):
    if total < 0:
        raise ValueError("order total cannot be negative")
    if total >= FREE_SHIPPING_THRESHOLD:
        return 0.0
    return FLAT_FEE
