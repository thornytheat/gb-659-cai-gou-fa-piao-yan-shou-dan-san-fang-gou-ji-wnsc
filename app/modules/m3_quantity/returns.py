"""退货数量勾稽：让主数据装箱规格参与箱→件折算。

场景：仓库退了一箱货，只记货号没记原收货批号，而该货号存在多版包装
（老 12 件/箱、新 10 件/箱）。直接按任一规格折算都可能多算或少算件数，
多算两件会导致红票多冲税款。批号缺失期间一律按最小规格保守折算，
少计的件数挂为待确认，等批号补齐后按实际规格追加。
"""
from decimal import Decimal

from .units import to_pieces


def return_piece_bounds(return_boxes: str, specs: list[dict]) -> dict:
    """根据全部装箱规格计算退货件数区间与当天可采信件数。

    specs 为 m2_master.pack_spec.pack_specs 的结果（已按件数升序）。
    - conservative_pieces：按最小规格折算，当天红票允许冲税的件数
    - maximum_pieces：按最大规格折算，真实退货件数的上界
    - pending_pieces：两者之差，即批号未齐时尚不能冲税的件数
    """
    boxes = Decimal(str(return_boxes))
    if boxes < 0:
        raise ValueError("NEGATIVE_QUANTITY")
    if not specs:
        raise ValueError("EMPTY_PACK_SPEC")
    converted = [
        {"pack_code": str(spec["pack_code"]),
         "pieces_per_box": str(Decimal(str(spec["pieces_per_box"]))),
         "pieces": str(to_pieces(str(boxes), "box", str(spec["pieces_per_box"])))}
        for spec in specs
    ]
    conservative = Decimal(converted[0]["pieces"])
    maximum = Decimal(converted[-1]["pieces"])
    return {
        "return_boxes": str(boxes),
        "conversions": converted,
        "conservative_pieces": str(conservative),
        "maximum_pieces": str(maximum),
        "pending_pieces": str(maximum - conservative),
    }


def allocate_return_to_receipt(returned_pieces: Decimal, received_pieces: Decimal) -> dict:
    """退货件数不得超过该货号累计验收件数（守 M3 既有守恒规则）。"""
    if returned_pieces < 0 or received_pieces < 0:
        raise ValueError("NEGATIVE_QUANTITY")
    if returned_pieces > received_pieces:
        raise ValueError("RETURN_EXCEEDS_RECEIPT")
    return {
        "returned_pieces": str(returned_pieces),
        "received_pieces": str(received_pieces),
        "net_received_pieces": str(received_pieces - returned_pieces),
    }
