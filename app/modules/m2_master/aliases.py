import unicodedata

def normalize_sku(value: str) -> str:
    return unicodedata.normalize("NFKC", str(value)).strip().upper().replace(" ", "")

def resolve_alias(value: str, aliases: dict[str, str]) -> str:
    current, visited = value, set()
    while current in aliases:
        if current in visited:
            raise ValueError("ALIAS_CYCLE")
        visited.add(current)
        current = aliases[current]
    return current

def normalize_supplier_code(value: str) -> str:
    token = str(value).strip()
    if not token.isdigit():
        raise ValueError("BAD_SUPPLIER_CODE")
    return token

