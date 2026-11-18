"""M7 退货红票：服务层（运行标识、台账持久化、幂等）。

幂等两道闸门：
1. 业务键 return_no 唯一：同一退货单重复登记直接复用既有台账；
2. 运行键 run_id 唯一（规则版本+输入摘要）：同一输入重跑复用同一运行，
   credit_events 唯一约束保证同一运行不会产生第二笔冲税。
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.config import RULE_VERSION
from app.manifest import input_digest
from app.reasons import REASONS
from app import store
from .ledger import evaluate_return, evaluate_batch_supplement

SHANGHAI = timezone(timedelta(hours=8))
_DATA_DIR = Path(__file__).resolve().parents[3] / "sample_data"


def _load_json(name: str) -> dict:
    with open(_DATA_DIR / name, encoding="utf-8") as handle:
        return json.load(handle)


# 主数据装箱规格与晚到批号索引的默认来源（可用同名结构在调用处覆盖）。
DEMO_REGISTRY = _load_json("pack_specs.json")
DEMO_BATCH_INDEX = _load_json("batch_index.json")


def _now() -> str:
    return datetime.now(SHANGHAI).isoformat(timespec="seconds")


def _run_id(stage: str, payload: dict) -> str:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"{RULE_VERSION}-m7-{stage}-{input_digest(body)[:12]}"


def register_return(payload: dict | None = None) -> dict:
    """当天登记退货并开具保守红票。"""
    payload = payload or {
        "return_no": "RT-20261118-01", "sku": "000142", "return_boxes": "1",
        "unit_price": "100.00", "tax_rate": "0.13", "received_pieces": "120",
    }
    required = ("return_no", "sku", "return_boxes", "unit_price", "tax_rate")
    missing = [key for key in required if not str(payload.get(key, "")).strip()]
    if missing:
        raise ValueError("EMPTY_VALUE")
    run_id = _run_id("register", payload)
    run_created = store.record_credit_event(run_id, payload["return_no"], "register", _now())

    existing = store.get_return_ledger(payload["return_no"])
    if existing is not None:
        return {
            "run_id": run_id, "created": False, "idempotent_replay": True,
            "reason_code": "DUPLICATE_RETURN",
            "reason_message": REASONS["DUPLICATE_RETURN"],
            "return": _serialize(existing),
            "batch_evidence": store.list_batch_evidence(payload["return_no"]),
        }

    evaluation = evaluate_return(
        payload["sku"], payload["return_boxes"], payload["unit_price"],
        payload["tax_rate"], payload.get("received_pieces"))
    timestamp = _now()
    record = {
        "return_no": payload["return_no"],
        "sku": payload["sku"],
        "tax_rate": evaluation["tax_rate"],
        "unit_price": evaluation["unit_price"],
        "return_boxes": evaluation["return_boxes"],
        "total_pieces": evaluation["maximum_pieces"],
        "conservative_pieces": evaluation["conservative_pieces"],
        "covered_pieces": evaluation["conservative_pieces"],
        "initial_tax": evaluation["initial_red_invoice"]["tax"],
        "added_tax": "0.00",
        "status": evaluation["status"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    saved = store.save_return_ledger(record)
    return {
        "run_id": run_id, "created": saved, "idempotent_replay": not run_created,
        "return": {**record, "outstanding": red_pending(record), **{
            "initial_red_invoice": evaluation["initial_red_invoice"],
            "pending_red_invoice": evaluation["pending_red_invoice"],
            "full_red_invoice_estimate": evaluation["full_red_invoice_estimate"],
            "conversions": evaluation["conversions"],
        }},
        "status": evaluation["status"],
        "basis": evaluation["basis"],
        "batch_evidence": [],
    }


def supplement_batch(payload: dict | None = None) -> dict:
    """收货批号补齐后追加冲税；同一批号重复提交不重复冲税。"""
    payload = payload or {
        "return_no": "RT-20261118-01",
        "batches": [{"batch_no": "LOT-20260901-07", "boxes": "1"}],
    }
    ledger = store.get_return_ledger(payload["return_no"])
    if ledger is None:
        raise ValueError("RETURN_NOT_FOUND")
    if not payload.get("batches"):
        raise ValueError("EMPTY_VALUE")
    run_id = _run_id("supplement", payload)
    run_created = store.record_credit_event(run_id, payload["return_no"], "supplement", _now())

    # 过滤掉本运行已登记或历史已登记的批号，保证重跑不重复冲税。
    known = {row["batch_no"]: row for row in store.list_batch_evidence(payload["return_no"])}
    fresh_batches = [batch for batch in payload["batches"] if batch["batch_no"] not in known]
    if not fresh_batches or not run_created:
        return {
            "run_id": run_id, "created": False, "idempotent_replay": True,
            "reason_code": "DUPLICATE_RETURN",
            "reason_message": "该运行或批号已登记，复用既有冲税结果，未重复冲税",
            "return": _serialize(ledger),
            "batch_evidence": store.list_batch_evidence(payload["return_no"]),
        }

    evaluation = evaluate_batch_supplement(
        ledger["sku"], ledger["return_boxes"], ledger["covered_pieces"],
        ledger["unit_price"], ledger["tax_rate"], fresh_batches,
        DEMO_BATCH_INDEX, DEMO_REGISTRY)
    for evidence in evaluation["evidence"]:
        store.record_batch_evidence({
            "return_no": payload["return_no"],
            "batch_no": evidence["batch_no"],
            "pack_code": evidence["pack_code"],
            "pieces_per_box": evidence["pieces_per_box"],
            "boxes": evidence["boxes"],
            "batch_pieces": evidence["batch_pieces"],
            "batch_tax": evidence["batch_tax"],
            "run_id": run_id,
        })
    store.update_return_progress(
        payload["return_no"], evaluation["new_covered_pieces"],
        str(_decimal(ledger["added_tax"]) + _decimal(evaluation["added_tax"])),
        evaluation["status"], _now())
    refreshed = store.get_return_ledger(payload["return_no"])
    return {
        "run_id": run_id, "created": True, "idempotent_replay": False,
        "supplement": evaluation,
        "return": _serialize(refreshed),
        "batch_evidence": store.list_batch_evidence(payload["return_no"]),
    }


def get_return(return_no: str) -> dict:
    ledger = store.get_return_ledger(return_no)
    if ledger is None:
        raise ValueError("RETURN_NOT_FOUND")
    evidence = store.list_batch_evidence(return_no)
    total_tax = _decimal(ledger["initial_tax"]) + _decimal(ledger["added_tax"])
    pending = red_pending(ledger)
    return {
        "return": _serialize(ledger),
        "accumulated_tax_offset": str(total_tax),
        "batch_evidence": evidence,
        "outstanding": pending,
        "basis": _query_basis(ledger, evidence),
    }


def red_pending(ledger: dict) -> dict:
    """还差多少税款未冲：按最大规格件数与已覆盖件数之差计算。"""
    from app.modules.m4_tax.red_invoice import remaining_tax
    return remaining_tax(ledger["total_pieces"], ledger["covered_pieces"],
                         ledger["unit_price"], ledger["tax_rate"])


def list_returns() -> dict:
    rows = store.list_return_ledger()
    items, outstanding_total = [], _decimal("0")
    for row in rows:
        pending = red_pending(row)
        outstanding_total += _decimal(pending["pending_tax"])
        items.append({
            "return_no": row["return_no"], "sku": row["sku"],
            "status": row["status"],
            "covered_pieces": row["covered_pieces"], "total_pieces": row["total_pieces"],
            "initial_tax": row["initial_tax"], "added_tax": row["added_tax"],
            "outstanding_tax": pending["pending_tax"],
        })
    return {"count": len(items), "outstanding_tax_total": str(outstanding_total), "items": items}


def _query_basis(ledger: dict, evidence: list[dict]) -> list[dict]:
    return [
        {"code": "MASTER_PACK_CONSERVATIVE",
         "message": REASONS["BATCH_PENDING"] if ledger["status"] == "BATCH_PENDING" else "批号已补齐，全部件数完成冲税",
         "detail": {"conservative_pieces": ledger["conservative_pieces"],
                    "total_pieces": ledger["total_pieces"],
                    "covered_pieces": ledger["covered_pieces"]}},
        {"code": "BATCH_EVIDENCE_LEDGER",
         "message": "晚到批号按实际包装规格逐批登记，批号+退货单唯一，重跑不重复冲税",
         "detail": evidence},
    ]


def _serialize(ledger: dict) -> dict:
    result = dict(ledger)
    result["outstanding"] = red_pending(ledger)
    return result


def _decimal(value: str):
    from decimal import Decimal
    return Decimal(str(value))
