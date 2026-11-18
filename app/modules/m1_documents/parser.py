REQUIRED = ("doc_type", "doc_no", "sku", "qty", "amount", "tax_rate")

def parse_documents(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    accepted, bad, seen = [], [], {}
    for line_no, row in enumerate(rows, 2):
        missing = [key for key in REQUIRED if not str(row.get(key, "")).strip()]
        if missing:
            bad.append({"line_no": line_no, "reason_code": "EMPTY_VALUE", "raw": row})
            continue
        key = (row["doc_type"], row["doc_no"], row["sku"], row["tax_rate"])
        if key in seen:
            code = "DUPLICATE_KEY" if seen[key] == row else "VALUE_CONFLICT"
            bad.append({"line_no": line_no, "reason_code": code, "raw": row})
            continue
        seen[key] = dict(row)
        accepted.append({**row, "line_no": line_no})
    return accepted, bad

def complete_tail(text: str) -> bool:
    return not text or text.endswith("\n")

