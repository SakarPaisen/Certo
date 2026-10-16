"""Stock levels for a small shop."""


class Inventory:
    def __init__(self):
        self._items = {}

    def add(self, sku, qty):
        self._items[sku] = self._items.get(sku, 0) + qty

    def remove(self, sku, qty):
        self._items[sku] = self._items[sku] - qty

    def quantity(self, sku):
        return self._items[sku]
