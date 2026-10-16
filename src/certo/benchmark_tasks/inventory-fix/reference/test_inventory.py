from inventory import Inventory


def test_add_then_quantity():
    inv = Inventory()
    inv.add("apple", 3)
    inv.add("apple", 2)
    assert inv.quantity("apple") == 5


def test_remove():
    inv = Inventory()
    inv.add("pear", 4)
    inv.remove("pear", 1)
    assert inv.quantity("pear") == 3
