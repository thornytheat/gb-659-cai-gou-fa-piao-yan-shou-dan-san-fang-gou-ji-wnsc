import pytest
from decimal import Decimal
from app.modules.m3_quantity.units import to_pieces, same_dimension
from app.modules.m3_quantity.match import quantity_account, reconcile_lines

def test_box_converts_to_pieces():
    assert to_pieces("3", "box", "12") == Decimal("36")

def test_kg_converts_to_grams():
    assert to_pieces("1.25", "kg") == Decimal("1250.00")

def test_negative_quantity_rejected():
    with pytest.raises(ValueError, match="NEGATIVE_QUANTITY"):
        to_pieces("-1", "piece")

def test_unknown_unit_rejected():
    with pytest.raises(ValueError, match="UNKNOWN_UNIT"):
        to_pieces("1", "pallet")

def test_open_quantity_accounts_for_returns():
    result = quantity_account(Decimal("10"), Decimal("9"), Decimal("1"))
    assert result["net_received"] == "8" and result["open"] == "2"

def test_return_cannot_exceed_receipt():
    with pytest.raises(ValueError, match="RETURN_EXCEEDS_RECEIPT"):
        quantity_account(Decimal("10"), Decimal("1"), Decimal("2"))

def test_line_reconciliation_is_conservative():
    assert reconcile_lines([{"ordered": "10", "net_received": "8", "open": "2"}])

