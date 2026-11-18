"""红票（红字发票）冲税额计算。

红票冲抵必须与蓝票口径一致：先按件数×不含税单价算净额并半入到分，
再用净额×税率半入到分，避免浮点尾差（TRAP-10）。
不同货号/税率分组各自计算，不互相抵消（TRAP-23）。
"""
from decimal import Decimal

from .calculate import money, tax_components


def red_invoice_tax(pieces: str, unit_price: str, tax_rate: str) -> dict:
    """给定退货件数，计算该部分可冲减的净额、税额与含税额。"""
    result = tax_components(pieces, unit_price, tax_rate)
    return {"pieces": str(Decimal(str(pieces))), **result}


def remaining_tax(total_pieces: str, covered_pieces: str, unit_price: str,
                  tax_rate: str) -> dict:
    """批号补齐后，计算尚未冲税的剩余件数对应税款。"""
    total, covered = Decimal(str(total_pieces)), Decimal(str(covered_pieces))
    if covered < 0 or total < 0 or covered > total:
        raise ValueError("BAD_COVERED_PIECES")
    pending_pieces = total - covered
    pending = red_invoice_tax(str(pending_pieces), unit_price, tax_rate)
    return {
        "total_pieces": str(total),
        "covered_pieces": str(covered),
        "pending_pieces": str(pending_pieces),
        "pending_net": pending["net"],
        "pending_tax": pending["tax"],
        "pending_gross": pending["gross"],
        "tax_rate": pending["tax_rate"],
    }


def accumulate_tax(amounts: list[str]) -> str:
    """累计已冲税额，Decimal 求和后半入到分。"""
    return str(money(sum((Decimal(value) for value in amounts), start=Decimal("0"))))
