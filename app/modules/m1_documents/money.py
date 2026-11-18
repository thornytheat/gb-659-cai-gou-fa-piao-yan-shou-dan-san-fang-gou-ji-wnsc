from decimal import Decimal, InvalidOperation

NULLS = {"", "-", "N/A", "NULL"}

def decimal_value(value: str) -> Decimal:
    token = str(value).strip().replace(",", "").replace("，", "").replace("￥", "")
    if token in NULLS:
        raise ValueError("EMPTY_AMOUNT")
    try:
        return Decimal(token)
    except InvalidOperation as exc:
        raise ValueError("BAD_AMOUNT") from exc

def normalize_rate(value: str) -> Decimal:
    token = str(value).strip().replace("%", "")
    result = Decimal(token)
    return result / 100 if result > 1 else result

