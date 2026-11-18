"""主数据：货号装箱规格（多包装版本）。

一个货号在生命周期内可能存在多版包装（如老包装 12 件/箱、新包装 10 件/箱）。
退货时只登记箱数、未登记原收货批号，无法确认对应哪一版包装，
因此主数据需要同时保留全部有效版本，勾稽时按最小规格保守折算。
"""
from decimal import Decimal

from .aliases import normalize_sku

# 装箱规格：pieces_per_box 为每箱件数，按字符串存储，Decimal 参与计算。
# 同一 sku 可挂多个 pack_code；effective_from 为该版包装启用日期（ISO 8601）。
PACK_REGISTRY: dict[str, list[dict]] = {
    "000142": [
        {"pack_code": "OLD-12", "pieces_per_box": "12", "effective_from": "2025-01-01"},
        {"pack_code": "NEW-10", "pieces_per_box": "10", "effective_from": "2026-06-01"},
    ],
    "SKU-B": [
        {"pack_code": "STD-10", "pieces_per_box": "10", "effective_from": "2025-01-01"},
    ],
    "SKU-C": [
        {"pack_code": "OLD-8", "pieces_per_box": "8", "effective_from": "2025-01-01"},
        {"pack_code": "NEW-6", "pieces_per_box": "6", "effective_from": "2026-09-01"},
    ],
}


def pack_specs(sku: str, registry: dict[str, list[dict]] | None = None) -> list[dict]:
    """返回货号的全部有效装箱规格（按每箱件数升序，保证择小稳定）。"""
    registry = PACK_REGISTRY if registry is None else registry
    canonical = normalize_sku(sku)
    if canonical not in registry:
        raise ValueError("UNKNOWN_SKU")
    return sorted(
        (dict(spec) for spec in registry[canonical]),
        key=lambda spec: (Decimal(str(spec["pieces_per_box"])), str(spec["pack_code"])),
    )


def smallest_pack(sku: str, registry: dict[str, list[dict]] | None = None) -> dict:
    """最小装箱规格：批号缺失时的保守折算依据。"""
    return pack_specs(sku, registry)[0]


def largest_pack(sku: str, registry: dict[str, list[dict]] | None = None) -> dict:
    """最大装箱规格：界定保守折算可能少计的退货件数上限。"""
    return pack_specs(sku, registry)[-1]


def resolve_batch_pack(sku: str, batch_no: str, batch_index: dict[str, dict],
                       registry: dict[str, list[dict]] | None = None) -> dict:
    """按晚到的收货批号定位该批货物实际对应的装箱规格。

    batch_index 结构：{batch_no: {"sku": ..., "pack_code": ...}}，
    批号必须归属该货号，且 pack_code 必须在主数据注册过，否则拒绝采信。
    """
    canonical = normalize_sku(sku)
    record = batch_index.get(str(batch_no).strip())
    if not record or normalize_sku(record.get("sku", "")) != canonical:
        raise ValueError("BATCH_NOT_FOUND")
    pack_code = str(record["pack_code"])
    for spec in pack_specs(canonical, registry):
        if str(spec["pack_code"]) == pack_code:
            return dict(spec)
    raise ValueError("PACK_CODE_NOT_REGISTERED")
