from .aliases import normalize_sku, resolve_alias
from .evolve import migrate_fields
from .pack_spec import pack_specs

ALIASES = {"OLD-A": "SKU-A", "A-01": "SKU-A"}

def run(payload: dict | None = None) -> dict:
    payload = migrate_fields(payload or {"item_code": " old-a ", "vendor_code": "000142"})
    normalized = normalize_sku(payload["sku"])
    canonical = resolve_alias(normalized, ALIASES)
    result = {"sku": normalized, "canonical": canonical, "supplier_code": str(payload["supplier_code"])}
    try:
        result["pack_specs"] = pack_specs(canonical)
    except ValueError:
        result["pack_specs"] = None  # 未注册装箱规格的货号，退货勾稽阶段会隔离 UNKNOWN_SKU
    return result

def demo():
    return run()

