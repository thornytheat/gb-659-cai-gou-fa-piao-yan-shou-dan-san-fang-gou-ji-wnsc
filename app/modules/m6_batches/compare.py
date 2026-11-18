from decimal import Decimal

def reconcile_amounts(received: str, invoiced: str, uninvoiced: str, difference: str) -> dict:
    values = [Decimal(value) for value in (received, invoiced, uninvoiced, difference)]
    balanced = values[0] == values[1] + values[2] + values[3]
    return {"received": str(values[0]), "invoiced": str(values[1]), "uninvoiced": str(values[2]), "difference": str(values[3]), "balanced": balanced}

def reconcile_counts(input_count: int, accepted: int, quarantined: int, duplicates: int) -> dict:
    return {"input": input_count, "accepted": accepted, "quarantined": quarantined, "duplicates": duplicates, "balanced": input_count == accepted + quarantined + duplicates}

