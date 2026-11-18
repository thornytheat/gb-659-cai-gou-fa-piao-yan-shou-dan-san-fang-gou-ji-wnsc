import json
import pytest
from pathlib import Path
from decimal import Decimal
from app.modules.m2_master.pack_spec import (
    pack_specs, smallest_pack, largest_pack, resolve_batch_pack, PACK_REGISTRY,
)

MULTI_SKU = "000142"  # 老包装 12 件/箱，新包装 10 件/箱

def test_pack_specs_sorted_ascending_by_pieces():
    specs = pack_specs(MULTI_SKU)
    assert [spec["pieces_per_box"] for spec in specs] == ["10", "12"]
    assert [spec["pack_code"] for spec in specs] == ["NEW-10", "OLD-12"]

def test_smallest_pack_is_conservative_basis():
    assert smallest_pack(MULTI_SKU)["pieces_per_box"] == "10"
    assert largest_pack(MULTI_SKU)["pieces_per_box"] == "12"

def test_unknown_sku_rejected():
    with pytest.raises(ValueError, match="UNKNOWN_SKU"):
        pack_specs("GHOST-9")

def test_batch_resolves_to_its_actual_pack():
    index = {"LOT-1": {"sku": MULTI_SKU, "pack_code": "OLD-12"}}
    spec = resolve_batch_pack(MULTI_SKU, "LOT-1", index)
    assert spec["pack_code"] == "OLD-12" and spec["pieces_per_box"] == "12"

def test_batch_of_other_sku_rejected():
    index = {"LOT-1": {"sku": "SKU-B", "pack_code": "STD-10"}}
    with pytest.raises(ValueError, match="BATCH_NOT_FOUND"):
        resolve_batch_pack(MULTI_SKU, "LOT-1", index)

def test_unregistered_pack_code_rejected():
    index = {"LOT-1": {"sku": MULTI_SKU, "pack_code": "LEGACY-99"}}
    with pytest.raises(ValueError, match="PACK_CODE_NOT_REGISTERED"):
        resolve_batch_pack(MULTI_SKU, "LOT-1", index)

def test_registry_covers_dual_packaging_scenario():
    assert len(PACK_REGISTRY["000142"]) == 2

def test_json_sample_matches_code_registry():
    sample = json.loads((Path(__file__).resolve().parents[1]
                         / "sample_data" / "pack_specs.json").read_text(encoding="utf-8"))
    for sku, specs in PACK_REGISTRY.items():
        assert sample[sku] == specs
