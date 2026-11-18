from .aliases import normalize_sku, resolve_alias
from .evolve import migrate_fields

ALIASES = {"OLD-A": "SKU-A", "A-01": "SKU-A"}

def run(payload: dict | None = None) -> dict:
    payload = migrate_fields(payload or {"item_code": " old-a ", "vendor_code": "000142"})
    normalized = normalize_sku(payload["sku"])
    return {"sku": normalized, "canonical": resolve_alias(normalized, ALIASES), "supplier_code": str(payload["supplier_code"])}

def demo():
    return run()

