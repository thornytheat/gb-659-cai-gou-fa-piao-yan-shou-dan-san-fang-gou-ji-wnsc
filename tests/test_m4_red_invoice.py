from decimal import Decimal
from app.modules.m4_tax.red_invoice import red_invoice_tax, remaining_tax, accumulate_tax

def test_red_invoice_tax_uses_blue_invoice_rule():
    result = red_invoice_tax("10", "100", "0.13")
    assert result["net"] == "1000.00"
    assert result["tax"] == "130.00"
    assert result["gross"] == "1130.00"

def test_two_extra_pieces_tax_is_twenty_six():
    # 老包装多出来的 2 件，13% 税率对应 26.00 元税款
    result = red_invoice_tax("2", "100", "0.13")
    assert result["net"] == "200.00" and result["tax"] == "26.00"

def test_remaining_tax_exposes_outstanding_amount():
    result = remaining_tax("12", "10", "100", "0.13")
    assert result["pending_pieces"] == "2"
    assert result["pending_tax"] == "26.00"

def test_remaining_zero_when_fully_covered():
    result = remaining_tax("10", "10", "100", "0.13")
    assert result["pending_pieces"] == "0" and result["pending_tax"] == "0.00"

def test_covered_above_total_rejected():
    import pytest
    with pytest.raises(ValueError, match="BAD_COVERED_PIECES"):
        remaining_tax("10", "11", "100", "0.13")

def test_accumulate_tax_sums_decimal():
    assert accumulate_tax(["130.00", "26.00"]) == "156.00"

def test_red_invoice_half_up_cent():
    # 3 件 × 33.33 = 99.99，税额 12.9987 → 半入到分 13.00
    result = red_invoice_tax("3", "33.33", "0.13")
    assert result["net"] == "99.99" and result["tax"] == "13.00"
