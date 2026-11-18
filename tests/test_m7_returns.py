import pytest
from fastapi.testclient import TestClient

import app.store as store
from app.main import app
from app.modules.m7_returns import service
from app.modules.m7_returns.ledger import evaluate_return, evaluate_batch_supplement

RETURN_PAYLOAD = {
    "return_no": "RT-20261118-01", "sku": "000142", "return_boxes": "1",
    "unit_price": "100.00", "tax_rate": "0.13", "received_pieces": "120",
}
SUPPLEMENT_PAYLOAD = {
    "return_no": "RT-20261118-01",
    "batches": [{"batch_no": "LOT-20260901-07", "boxes": "1"}],
}


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATABASE_PATH", tmp_path / "returns.sqlite3")
    return tmp_path


# ---------- 纯计算：当天保守评估 ----------

def test_same_day_conservative_red_invoice_uses_smallest_pack():
    result = evaluate_return("000142", "1", "100.00", "0.13", "120",
                             service.DEMO_REGISTRY)
    # 不是 12 件：多算两件会多冲 26 元税
    assert result["conservative_pieces"] == "10"
    assert result["maximum_pieces"] == "12"
    assert result["initial_red_invoice"]["tax"] == "130.00"
    assert result["pending_red_invoice"]["pending_tax"] == "26.00"
    assert result["status"] == "BATCH_PENDING"

def test_basis_explains_how_much_tax_and_why():
    result = evaluate_return("000142", "1", "100.00", "0.13", "120",
                             service.DEMO_REGISTRY)
    codes = [item["code"] for item in result["basis"]]
    assert codes == ["PACK_SPEC_FROM_MASTER", "CONSERVATIVE_PACK_RULE",
                     "TAX_SAME_AS_BLUE_INVOICE", "PENDING_UNTIL_BATCH"]
    rule = next(item for item in result["basis"] if item["code"] == "CONSERVATIVE_PACK_RULE")
    assert rule["detail"]["formula"] == "1 箱 × 10 件/箱"

def test_return_exceeding_receipt_rejected():
    with pytest.raises(ValueError, match="RETURN_EXCEEDS_RECEIPT"):
        evaluate_return("000142", "99", "100.00", "0.13", "120",
                        service.DEMO_REGISTRY)

def test_unknown_sku_rejected():
    with pytest.raises(ValueError, match="UNKNOWN_SKU"):
        evaluate_return("NO-SUCH", "1", "100.00", "0.13")


# ---------- 纯计算：批号补齐 ----------

def test_supplement_only_charges_delta_pieces():
    result = evaluate_batch_supplement(
        "000142", "1", "10", "100.00", "0.13",
        SUPPLEMENT_PAYLOAD["batches"], service.DEMO_BATCH_INDEX,
        service.DEMO_REGISTRY)
    # 老包装实际 12 件，已冲 10 件，只追加 2 件 / 26.00 元
    assert result["actual_total_pieces"] == "12"
    assert result["added_pieces"] == "2"
    assert result["added_tax"] == "26.00"
    assert result["status"] == "FULLY_COVERED"
    assert result["remaining"]["pending_tax"] == "0.00"

def test_supplement_boxes_must_cover_full_return():
    with pytest.raises(ValueError, match="BATCH_BOXES_MISMATCH"):
        evaluate_batch_supplement(
            "000142", "1", "10", "100.00", "0.13",
            [{"batch_no": "LOT-20260901-07", "boxes": "0.5"}],
            service.DEMO_BATCH_INDEX, service.DEMO_REGISTRY)

def test_supplement_rejects_foreign_batch():
    with pytest.raises(ValueError, match="BATCH_NOT_FOUND"):
        evaluate_batch_supplement(
            "000142", "1", "10", "100.00", "0.13",
            [{"batch_no": "LOT-UNKNOWN", "boxes": "1"}],
            service.DEMO_BATCH_INDEX, service.DEMO_REGISTRY)


# ---------- 服务层 + 落库 + 幂等 ----------

def test_full_lifecycle_and_idempotent_rerun(isolated_db):
    first = service.register_return(RETURN_PAYLOAD)
    assert first["created"] is True
    assert first["return"]["initial_tax"] == "130.00"
    assert first["return"]["covered_pieces"] == "10"
    assert first["return"]["status"] == "BATCH_PENDING"
    assert first["return"]["outstanding"]["pending_tax"] == "26.00"

    # 重跑同一笔退货：复用台账，不产生第二张红票
    replay = service.register_return(RETURN_PAYLOAD)
    assert replay["created"] is False
    assert replay["idempotent_replay"] is True
    assert replay["reason_code"] == "DUPLICATE_RETURN"
    assert replay["return"]["initial_tax"] == "130.00"

    # 批号补齐：追加 2 件、26.00 元
    supplemented = service.supplement_batch(SUPPLEMENT_PAYLOAD)
    assert supplemented["created"] is True
    assert supplemented["supplement"]["added_tax"] == "26.00"
    assert supplemented["return"]["covered_pieces"] == "12"
    assert supplemented["return"]["status"] == "FULLY_COVERED"

    # 重跑补齐：不重复冲税
    replay_supplement = service.supplement_batch(SUPPLEMENT_PAYLOAD)
    assert replay_supplement["created"] is False
    assert replay_supplement["idempotent_replay"] is True
    ledger = store.get_return_ledger("RT-20261118-01")
    assert ledger["added_tax"] == "26.00"  # 没有被第二遍累加成 52.00
    assert len(store.list_batch_evidence("RT-20261118-01")) == 1

def test_query_reports_outstanding_tax_before_and_after(isolated_db):
    service.register_return(RETURN_PAYLOAD)
    pending = service.get_return("RT-20261118-01")
    assert pending["outstanding"]["pending_tax"] == "26.00"
    assert pending["accumulated_tax_offset"] == "130.00"

    service.supplement_batch(SUPPLEMENT_PAYLOAD)
    closed = service.get_return("RT-20261118-01")
    assert closed["outstanding"]["pending_tax"] == "0.00"
    assert closed["accumulated_tax_offset"] == "156.00"
    assert closed["batch_evidence"][0]["pack_code"] == "OLD-12"

def test_list_aggregates_outstanding_tax(isolated_db):
    service.register_return(RETURN_PAYLOAD)
    summary = service.list_returns()
    assert summary["count"] == 1
    assert summary["outstanding_tax_total"] == "26.00"

def test_supplement_unknown_return_rejected(isolated_db):
    with pytest.raises(ValueError, match="RETURN_NOT_FOUND"):
        service.supplement_batch({"return_no": "GHOST", "batches": SUPPLEMENT_PAYLOAD["batches"]})

def test_register_missing_field_rejected(isolated_db):
    with pytest.raises(ValueError, match="EMPTY_VALUE"):
        service.register_return({"return_no": "RT-X", "sku": "000142"})


# ---------- HTTP 接口 ----------

def test_http_pages_and_endpoints(isolated_db):
    client = TestClient(app)
    assert client.get("/returns").status_code == 200

    resp = client.post("/api/returns/register", json=RETURN_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["return"]["initial_tax"] == "130.00"

    replay = client.post("/api/returns/register", json=RETURN_PAYLOAD)
    assert replay.json()["idempotent_replay"] is True

    supplement = client.post("/api/returns/supplement", json=SUPPLEMENT_PAYLOAD)
    assert supplement.status_code == 200
    assert supplement.json()["supplement"]["added_tax"] == "26.00"

    detail = client.get("/api/returns/RT-20261118-01").json()
    assert detail["accumulated_tax_offset"] == "156.00"
    assert detail["outstanding"]["pending_tax"] == "0.00"

    listing = client.get("/api/returns").json()
    assert listing["items"][0]["status"] == "FULLY_COVERED"

def test_http_unknown_sku_returns_422(isolated_db):
    client = TestClient(app)
    resp = client.post("/api/returns/register",
                       json={**RETURN_PAYLOAD, "return_no": "RT-BAD", "sku": "GHOST"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "UNKNOWN_SKU"

def test_http_get_missing_return_returns_404(isolated_db):
    client = TestClient(app)
    assert client.get("/api/returns/NO-SUCH").status_code == 404
