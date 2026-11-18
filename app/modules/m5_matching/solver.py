from decimal import Decimal
from itertools import combinations

def subset_match(rows: list[dict], target: Decimal, tolerance: Decimal = Decimal("0.01"), limit: int = 4) -> list[dict]:
    matches = []
    for size in range(1, min(limit, len(rows)) + 1):
        for group in combinations(rows, size):
            total = sum((Decimal(row["amount"]) for row in group), start=Decimal("0"))
            difference = abs(total - target)
            if difference <= tolerance:
                key = (difference, size, tuple(sorted(row["id"] for row in group)))
                matches.append((key, list(group)))
    return min(matches, key=lambda item: item[0])[1] if matches else []

def matched_total(rows: list[dict]) -> Decimal:
    return sum((Decimal(row["amount"]) for row in rows), start=Decimal("0"))

