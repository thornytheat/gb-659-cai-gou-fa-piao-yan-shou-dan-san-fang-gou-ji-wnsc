import pytest
from app.modules.m2_master.aliases import normalize_sku, resolve_alias, normalize_supplier_code
from app.modules.m2_master.evolve import migrate_fields, required_present

def test_fullwidth_sku_normalizes():
    assert normalize_sku(" Ａ－０１ ") == "A-01"

def test_alias_chain_resolves():
    assert resolve_alias("OLD", {"OLD": "MID", "MID": "NEW"}) == "NEW"

def test_alias_cycle_rejected():
    with pytest.raises(ValueError, match="ALIAS_CYCLE"):
        resolve_alias("A", {"A": "B", "B": "A"})

def test_supplier_code_preserves_leading_zero():
    assert normalize_supplier_code("000142") == "000142"  # TRAP-08

def test_bad_supplier_code_rejected():
    with pytest.raises(ValueError, match="BAD_SUPPLIER_CODE"):
        normalize_supplier_code("14A")

def test_old_columns_migrate():
    row = migrate_fields({"item_code": "A", "vendor_code": "001"})
    assert row == {"sku": "A", "supplier_code": "001"}  # TRAP-17

def test_conflicting_old_and_new_fields_rejected():
    with pytest.raises(ValueError, match="FIELD_CONFLICT"):
        migrate_fields({"item_code": "A", "sku": "B"})

