from decimal import Decimal

UNIT_FACTORS = {"piece": Decimal("1"), "kg": Decimal("1000"), "g": Decimal("1")}

def to_pieces(quantity: str, unit: str, pack_size: str = "1") -> Decimal:
    value = Decimal(str(quantity))
    if value < 0:
        raise ValueError("NEGATIVE_QUANTITY")
    if unit == "box":
        return value * Decimal(str(pack_size))
    if unit not in UNIT_FACTORS:
        raise ValueError("UNKNOWN_UNIT")
    return value * UNIT_FACTORS[unit]

def same_dimension(left: str, right: str) -> bool:
    weight = {"kg", "g"}
    return left == right or {left, right}.issubset(weight)

