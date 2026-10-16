"""Stock levels for a small shop."""


class OutOfStock(ValueError):
    pass


def _check_qty(qty):
    if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
        raise ValueError(f"quantity must be a positive int, got {qty!r}")


class Inventory:
    def __init__(self):
        self._items = {}

    def add(self, sku, qty):
        _check_qty(qty)
        self._items[sku] = self._items.get(sku, 0) + qty

    def remove(self, sku, qty):
        _check_qty(qty)
        have = self._items.get(sku, 0)
        if qty > have:
            raise OutOfStock(f"only {have} of {sku!r} in stock")
        if have == qty:
            del self._items[sku]
        else:
            self._items[sku] = have - qty

    def quantity(self, sku):
        return self._items.get(sku, 0)

    def skus(self):
        return sorted(self._items)

    def low_stock(self, threshold):
        return sorted((sku, qty) for sku, qty in self._items.items() if qty <= threshold)
