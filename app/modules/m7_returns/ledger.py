"""M7 退货红票：核心编排（纯计算，不落库）。

串联：
- M2 主数据装箱规格（pack_spec）确定多版包装的件数区间；
- M3 退货勾稽（returns）按最小规格保守折算件数；
- M4 红票税额（red_invoice）按蓝票同口径算可冲税额。
"""
from decimal import Decimal

from app.modules.m2_master.pack_spec import pack_specs, resolve_batch_pack
from app.modules.m3_quantity.returns import return_piece_bounds, allocate_return_to_receipt
from app.modules.m3_quantity.units import to_pieces
from app.modules.m4_tax.red_invoice import red_invoice_tax, remaining_tax


def evaluate_return(sku: str, return_boxes: str, unit_price: str, tax_rate: str,
                    received_pieces: str | None = None,
                    registry: dict | None = None) -> dict:
    """批号缺失当天的保守红票评估。"""
    specs = pack_specs(sku, registry)
    bounds = return_piece_bounds(return_boxes, specs)
    maximum = Decimal(bounds["maximum_pieces"])
    if received_pieces is not None:
        # 退货总量上界也不得超过累计验收，防止凭退货虚冲。
        allocate_return_to_receipt(maximum, Decimal(str(received_pieces)))
    initial = red_invoice_tax(bounds["conservative_pieces"], unit_price, tax_rate)
    pending = remaining_tax(bounds["maximum_pieces"], bounds["conservative_pieces"],
                            unit_price, tax_rate)
    full = red_invoice_tax(bounds["maximum_pieces"], unit_price, tax_rate)
    status = "FULLY_COVERED" if Decimal(bounds["pending_pieces"]) == 0 else "BATCH_PENDING"
    basis = [
        {"code": "PACK_SPEC_FROM_MASTER",
         "message": "装箱规格取自货号主数据，全部有效包装版本均参与勾稽",
         "detail": specs},
        {"code": "CONSERVATIVE_PACK_RULE",
         "message": "原收货批号缺失，按最小装箱规格保守折算当天可冲税件数，避免多冲税款",
         "detail": {"return_boxes": bounds["return_boxes"],
                    "chosen_pack_code": specs[0]["pack_code"],
                    "pieces_per_box": specs[0]["pieces_per_box"],
                    "formula": f"{bounds['return_boxes']} 箱 × {specs[0]['pieces_per_box']} 件/箱"}},
        {"code": "TAX_SAME_AS_BLUE_INVOICE",
         "message": "红票口径与蓝票一致：净额=件数×不含税单价（半入到分），税额=净额×税率（半入到分）",
         "detail": {"unit_price": str(Decimal(str(unit_price))), "tax_rate": str(Decimal(str(tax_rate)))}},
        {"code": "PENDING_UNTIL_BATCH",
         "message": "按最大规格折算的件数与保守件数之差挂账，待收货批号补齐后按实际包装追加冲税",
         "detail": {"pending_pieces": bounds["pending_pieces"],
                    "pending_tax": pending["pending_tax"]}},
    ]
    return {
        "sku": sku,
        "tax_rate": str(Decimal(str(tax_rate))),
        "unit_price": str(Decimal(str(unit_price))),
        "pack_specs": specs,
        **bounds,
        "initial_red_invoice": initial,
        "pending_red_invoice": pending,
        "full_red_invoice_estimate": full,
        "status": status,
        "basis": basis,
    }


def evaluate_batch_supplement(sku: str, return_boxes_total: str, covered_pieces: str,
                              unit_price: str, tax_rate: str,
                              batches: list[dict], batch_index: dict,
                              registry: dict | None = None) -> dict:
    """批号补齐后的追加冲税评估。

    batches: [{"batch_no": "...", "boxes": "1"}]，批号→包装的映射取自 batch_index。
    补齐的批号必须解释全部退货箱数（箱数守恒）；实际总件数落于
    [保守件数, 最大件数] 区间内。追加冲税额只对“实际件数−已覆盖件数”
    的差额计税，绝不整箱重复计。
    """
    specs = pack_specs(sku, registry)
    bounds = return_piece_bounds(return_boxes_total, specs)
    maximum_pieces = Decimal(bounds["maximum_pieces"])
    conservative_pieces = Decimal(bounds["conservative_pieces"])
    return_boxes = Decimal(bounds["return_boxes"])
    covered = Decimal(str(covered_pieces))

    evidence, actual_boxes, actual_total = [], Decimal("0"), Decimal("0")
    for batch in batches:
        spec = resolve_batch_pack(sku, batch["batch_no"], batch_index, registry)
        boxes = Decimal(str(batch["boxes"]))
        batch_pieces = to_pieces(str(boxes), "box", spec["pieces_per_box"])
        batch_tax = red_invoice_tax(str(batch_pieces), unit_price, tax_rate)
        actual_boxes += boxes
        actual_total += batch_pieces
        evidence.append({
            "batch_no": str(batch["batch_no"]),
            "pack_code": spec["pack_code"],
            "pieces_per_box": spec["pieces_per_box"],
            "boxes": str(boxes),
            "batch_pieces": str(batch_pieces),
            "batch_net": batch_tax["net"],
            "batch_tax": batch_tax["tax"],
            "batch_gross": batch_tax["gross"],
        })

    if actual_boxes != return_boxes:
        raise ValueError("BATCH_BOXES_MISMATCH")
    if not conservative_pieces <= actual_total <= maximum_pieces:
        raise ValueError("BATCH_PIECES_EXCEED_RETURN")
    added_pieces = actual_total - covered
    if added_pieces < 0:
        raise ValueError("BATCH_PIECES_EXCEED_RETURN")
    delta_tax = red_invoice_tax(str(added_pieces), unit_price, tax_rate)
    remaining = remaining_tax(str(actual_total), str(actual_total), unit_price, tax_rate)
    return {
        "actual_total_pieces": str(actual_total),
        "added_pieces": str(added_pieces),
        "added_net": delta_tax["net"],
        "added_tax": delta_tax["tax"],
        "added_gross": delta_tax["gross"],
        "new_covered_pieces": str(actual_total),
        "total_pieces": str(actual_total),
        "status": "FULLY_COVERED",
        "remaining": remaining,
        "evidence": evidence,
    }
