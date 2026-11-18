from .parser import parse_documents
from .money import decimal_value

SAMPLE = [{"doc_type": "PO", "doc_no": "PO-001", "sku": "000142", "qty": "10", "amount": "1,000.00", "tax_rate": "0.13"}]

def run(rows: list[dict] | None = None) -> dict:
    accepted, quarantined = parse_documents(rows or SAMPLE)
    total = sum((decimal_value(row["amount"]) for row in accepted), start=decimal_value("0"))
    return {"input": len(accepted) + len(quarantined), "accepted": len(accepted), "quarantined": len(quarantined), "amount": str(total), "evidence": quarantined}

def demo():
    return run()

