import pytest
from decimal import Decimal
from app.modules.m3_quantity.returns import return_piece_bounds, allocate_return_to_receipt

DUAL_SPECS = [
    {"pack_code": "NEW-10", "pieces_per_box": "10", "effective_from": "2026-06-01"},
    {"pack_code": "OLD-12", "pieces_per_box": "12", "effective_from": "2025-01-01"},
]

def test_one_box_conservative_is_ten_not_twelve():
    # 一箱退货、批号缺失：只能按最小规格 10 件保守采信，2 件挂账
    result = return_piece_bounds("1", DUAL_SPECS)
    assert result["conservative_pieces"] == "10"
    assert result["maximum_pieces"] == "12"
    assert result["pending_pieces"] == "2"

def test_every_pack_version_participates_in_reconciliation():
    result = return_piece_bounds("1", DUAL_SPECS)
    assert {row["pack_code"]: row["pieces"] for row in result["conversions"]} == {
        "NEW-10": "10", "OLD-12": "12",
    }

def test_multi_box_bounds_scale_linearly():
    result = return_piece_bounds("3", DUAL_SPECS)
    assert result["conservative_pieces"] == "30"
    assert result["maximum_pieces"] == "36"
    assert result["pending_pieces"] == "6"

def test_negative_boxes_rejected():
    with pytest.raises(ValueError, match="NEGATIVE_QUANTITY"):
        return_piece_bounds("-1", DUAL_SPECS)

def test_empty_spec_rejected():
    with pytest.raises(ValueError, match="EMPTY_PACK_SPEC"):
        return_piece_bounds("1", [])

def test_return_cannot_exceed_received_pieces():
    with pytest.raises(ValueError, match="RETURN_EXCEEDS_RECEIPT"):
        allocate_return_to_receipt(Decimal("13"), Decimal("12"))

def test_allocation_leaves_net_received():
    result = allocate_return_to_receipt(Decimal("12"), Decimal("120"))
    assert result["net_received_pieces"] == "108"
