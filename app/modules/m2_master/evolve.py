FIELD_ALIASES = {"item_code": "sku", "vendor_code": "supplier_code", "vat": "tax_rate"}

def migrate_fields(row: dict) -> dict:
    result = dict(row)
    for old, new in FIELD_ALIASES.items():
        if old in result and new not in result:
            result[new] = result.pop(old)
        elif old in result and new in result and result[old] != result[new]:
            raise ValueError("FIELD_CONFLICT")
    return result

def required_present(row: dict, fields: tuple[str, ...]) -> bool:
    return all(field in row and str(row[field]).strip() for field in fields)

