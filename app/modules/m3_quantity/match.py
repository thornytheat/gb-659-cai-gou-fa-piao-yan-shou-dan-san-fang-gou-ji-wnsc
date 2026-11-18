from decimal import Decimal

def quantity_account(ordered: Decimal, received: Decimal, returned: Decimal) -> dict:
    net_received = received - returned
    if net_received < 0:
        raise ValueError("RETURN_EXCEEDS_RECEIPT")
    open_qty = ordered - net_received
    status = "OVER_RECEIVED" if open_qty < 0 else "BALANCED" if open_qty == 0 else "OPEN"
    return {"ordered": str(ordered), "received": str(received), "returned": str(returned), "net_received": str(net_received), "open": str(open_qty), "status": status}

def reconcile_lines(lines: list[dict]) -> bool:
    return all(Decimal(line["ordered"]) == Decimal(line["net_received"]) + Decimal(line["open"]) for line in lines)

