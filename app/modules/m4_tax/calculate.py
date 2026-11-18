from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")

def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)

def tax_components(quantity: str, unit_price: str, tax_rate: str) -> dict:
    qty, price, rate = Decimal(quantity), Decimal(unit_price), Decimal(tax_rate)
    if qty < 0 or price < 0 or rate < 0:
        raise ValueError("NEGATIVE_COMPONENT")
    net = money(qty * price)
    tax = money(net * rate)
    gross = net + tax
    return {"net": str(net), "tax": str(tax), "gross": str(gross), "tax_rate": str(rate)}

def sum_money(values: list[str]) -> str:
    return str(money(sum((Decimal(value) for value in values), start=Decimal("0"))))

