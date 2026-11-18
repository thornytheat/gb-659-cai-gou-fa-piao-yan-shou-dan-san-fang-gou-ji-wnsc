from decimal import Decimal

def grouped_candidates(receipts: list[dict], invoice: dict) -> list[dict]:
    return sorted([row for row in receipts if row["sku"] == invoice["sku"] and Decimal(str(row["tax_rate"])) == Decimal(str(invoice["tax_rate"]))], key=lambda row: (Decimal(row["amount"]), row["id"]), reverse=True)

def within_window(left_date, right_date, days: int = 90) -> bool:
    return abs((left_date - right_date).days) <= days

