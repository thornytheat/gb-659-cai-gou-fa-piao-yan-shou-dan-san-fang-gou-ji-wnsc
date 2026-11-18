import pytest
from app.modules.m1_documents.parser import parse_documents, complete_tail
from app.modules.m1_documents.money import decimal_value, normalize_rate

BASE = {"doc_type": "PO", "doc_no": "001", "sku": "000142", "qty": "1", "amount": "1,000.00", "tax_rate": "13%"}

def test_clean_document_accepted():
    good, bad = parse_documents([BASE])
    assert len(good) == 1 and not bad and good[0]["line_no"] == 2

def test_missing_field_quarantined():
    good, bad = parse_documents([{**BASE, "sku": ""}])
    assert not good and bad[0]["reason_code"] == "EMPTY_VALUE"  # TRAP-05 TRAP-07

def test_exact_duplicate_detected():
    good, bad = parse_documents([BASE, BASE])
    assert len(good) == 1 and bad[0]["reason_code"] == "DUPLICATE_KEY"

def test_conflicting_duplicate_detected():
    good, bad = parse_documents([BASE, {**BASE, "amount": "2.00"}])
    assert bad[0]["reason_code"] == "VALUE_CONFLICT"  # TRAP-14

def test_thousands_amount_uses_decimal():
    assert decimal_value("1,234.50") == decimal_value("1234.50")  # TRAP-06

def test_percent_rate_normalizes():
    assert normalize_rate("13%") == decimal_value("0.13")

def test_tail_must_end_on_record_boundary():
    assert complete_tail("x\n") and not complete_tail("x")

