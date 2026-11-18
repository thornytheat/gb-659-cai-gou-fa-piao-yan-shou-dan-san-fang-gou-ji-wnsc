from decimal import Decimal
from datetime import date
from app.modules.m5_matching.candidates import grouped_candidates, within_window
from app.modules.m5_matching.solver import subset_match, matched_total

ROWS = [{"id": "B", "sku": "A", "tax_rate": "0.13", "amount": "40"}, {"id": "A", "sku": "A", "tax_rate": "0.13", "amount": "60"}, {"id": "C", "sku": "A", "tax_rate": "0.09", "amount": "100"}]

def test_candidates_stay_in_tax_group():
    result = grouped_candidates(ROWS, {"sku": "A", "tax_rate": "0.13"})
    assert [row["id"] for row in result] == ["A", "B"]

def test_date_window_inclusive():
    assert within_window(date(2026, 1, 1), date(2026, 4, 1), 90)

def test_subset_two_to_one():
    selected = subset_match(ROWS[:2], Decimal("100"))
    assert {row["id"] for row in selected} == {"A", "B"}

def test_no_match_returns_empty():
    assert subset_match(ROWS[:2], Decimal("99"), Decimal("0")) == []

def test_tolerance_boundary_included():
    assert subset_match([{"id": "A", "amount": "99.99"}], Decimal("100.00"), Decimal("0.01"))

def test_choice_is_order_independent():
    left = subset_match(ROWS[:2], Decimal("100"))
    right = subset_match(list(reversed(ROWS[:2])), Decimal("100"))
    assert sorted(x["id"] for x in left) == sorted(x["id"] for x in right)  # TRAP-19

def test_matched_total_is_decimal():
    assert matched_total(ROWS[:2]) == Decimal("100")

