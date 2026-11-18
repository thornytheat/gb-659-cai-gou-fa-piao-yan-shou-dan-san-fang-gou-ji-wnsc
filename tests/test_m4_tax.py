import pytest
from decimal import Decimal
from app.modules.m4_tax.calculate import money, tax_components, sum_money
from app.modules.m4_tax.verify import verify_invoice, same_tax_group

def test_tax_components_sum_exactly():
    result = tax_components("10", "100", "0.13")
    assert result == {"net": "1000.00", "tax": "130.00", "gross": "1130.00", "tax_rate": "0.13"}

def test_half_up_to_cent():
    assert money(Decimal("1.005")) == Decimal("1.01")  # TRAP-10

def test_negative_component_rejected():
    with pytest.raises(ValueError, match="NEGATIVE_COMPONENT"):
        tax_components("-1", "100", "0.13")

def test_sum_money_avoids_float_error():
    assert sum_money(["0.10", "0.20"]) == "0.30"

def test_one_cent_tolerance_passes():
    assert verify_invoice("100.00", "100.01")["status"] == "PASS"

def test_larger_tax_difference_fails():
    assert verify_invoice("100.00", "100.02")["status"] == "TAX_DIFFERENCE"

def test_different_tax_rates_never_offset():
    left = {"sku": "A", "tax_rate": "0.13"}; right = {"sku": "A", "tax_rate": "0.09"}
    assert not same_tax_group(left, right)  # TRAP-23

