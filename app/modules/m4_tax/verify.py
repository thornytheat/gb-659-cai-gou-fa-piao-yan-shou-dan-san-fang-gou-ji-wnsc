from decimal import Decimal

def verify_invoice(calculated_gross: str, invoice_gross: str, tolerance: str = "0.01") -> dict:
    difference = Decimal(invoice_gross) - Decimal(calculated_gross)
    status = "PASS" if abs(difference) <= Decimal(tolerance) else "TAX_DIFFERENCE"
    return {"invoice_gross": str(Decimal(invoice_gross)), "difference": str(difference), "status": status}

def same_tax_group(left: dict, right: dict) -> bool:
    return left["sku"] == right["sku"] and Decimal(str(left["tax_rate"])) == Decimal(str(right["tax_rate"]))

