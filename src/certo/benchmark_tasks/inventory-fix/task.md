# Fix and extend the inventory

This folder has a small Python module, `inventory.py`, and its tests. Fix
its bugs and add two features. Use only the standard library, and keep the
existing tests passing.

Required behaviour of `Inventory`:

1. `quantity(sku)` returns 0 for a SKU it has never seen (today it
   crashes).
2. `add(sku, qty)` and `remove(sku, qty)` accept only an `int` greater
   than zero as `qty`. Anything else (0, a negative number, a float, a
   string, `True`/`False`) raises `ValueError` and changes nothing.
3. Removing more than is in stock, or removing a SKU that isn't in stock,
   raises `OutOfStock` and changes nothing. Define `OutOfStock` in
   `inventory.py` as a subclass of `ValueError`.
4. A SKU whose quantity reaches 0 is no longer in stock.
5. New method `skus()`: the sorted list of SKUs in stock (quantity above
   0).
6. New method `low_stock(threshold)`: a sorted list of `(sku, quantity)`
   pairs for the SKUs in stock whose quantity is less than or equal to
   `threshold`.

Add tests for the new behaviour to `test_inventory.py`.
