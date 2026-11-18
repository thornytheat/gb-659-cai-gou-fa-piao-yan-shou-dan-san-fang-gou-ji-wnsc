from .calculate import tax_components
from .verify import verify_invoice

def run(payload: dict | None = None) -> dict:
    payload = payload or {"quantity": "10", "unit_price": "100", "tax_rate": "0.13", "gross": "1130.00"}
    calculated = tax_components(payload["quantity"], payload["unit_price"], payload["tax_rate"])
    return {**calculated, **verify_invoice(calculated["gross"], payload["gross"])}

def demo():
    return run()

