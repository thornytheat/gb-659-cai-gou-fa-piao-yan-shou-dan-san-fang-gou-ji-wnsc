from decimal import Decimal
from .candidates import grouped_candidates
from .solver import subset_match

def run() -> dict:
    receipts = [{"id": "GR-1", "sku": "SKU-A", "tax_rate": "0.13", "amount": "600.00"}, {"id": "GR-2", "sku": "SKU-A", "tax_rate": "0.13", "amount": "530.00"}]
    invoice = {"id": "IV-1", "sku": "SKU-A", "tax_rate": "0.13", "amount": "1130.00"}
    candidates = grouped_candidates(receipts, invoice)
    selected = subset_match(candidates, Decimal(invoice["amount"]))
    return {"invoice": invoice["id"], "matched": [row["id"] for row in selected], "amount": str(sum((Decimal(row["amount"]) for row in selected), start=Decimal("0")))}

def demo():
    return run()

