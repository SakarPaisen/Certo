import pytest
from inventory import Inventory, OutOfStock


def stocked():
    inv = Inventory()
    inv.add("apple", 5)
    inv.add("pear", 2)
    inv.add("kiwi", 10)
    return inv


def test_existing_behaviour_still_works():
    inv = Inventory()
    inv.add("apple", 3)
    inv.add("apple", 2)
    inv.remove("apple", 1)
    assert inv.quantity("apple") == 4


def test_unknown_sku_has_zero():
    assert Inventory().quantity("ghost") == 0


@pytest.mark.parametrize("qty", [0, -1, 1.5, "2", True, False, None])
def test_bad_quantities_are_rejected_and_change_nothing(qty):
    inv = stocked()
    with pytest.raises(ValueError):
        inv.add("apple", qty)
    with pytest.raises(ValueError):
        inv.remove("apple", qty)
    assert inv.quantity("apple") == 5


def test_out_of_stock_is_a_value_error():
    assert issubclass(OutOfStock, ValueError)


def test_removing_too_much_raises_and_changes_nothing():
    inv = stocked()
    with pytest.raises(OutOfStock):
        inv.remove("pear", 3)
    assert inv.quantity("pear") == 2


def test_removing_unknown_sku_raises():
    with pytest.raises(OutOfStock):
        Inventory().remove("ghost", 1)


def test_sku_at_zero_is_no_longer_in_stock():
    inv = stocked()
    inv.remove("pear", 2)
    assert inv.quantity("pear") == 0
    assert "pear" not in inv.skus()
    with pytest.raises(OutOfStock):
        inv.remove("pear", 1)


def test_skus_are_sorted():
    assert stocked().skus() == ["apple", "kiwi", "pear"]
    assert Inventory().skus() == []


def test_low_stock():
    inv = stocked()
    assert inv.low_stock(5) == [("apple", 5), ("pear", 2)]
    assert inv.low_stock(1) == []
    inv.remove("kiwi", 9)
    assert inv.low_stock(1) == [("kiwi", 1)]
