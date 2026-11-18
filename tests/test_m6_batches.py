from app.manifest import build_manifest, run_id
from app.modules.m6_batches.compare import reconcile_amounts, reconcile_counts
from app.modules.m6_batches.exporter import differences_csv
import app.store as store

def test_amounts_balance():
    assert reconcile_amounts("100", "80", "20", "0")["balanced"]

def test_amount_difference_visible():
    assert not reconcile_amounts("100", "80", "19", "0")["balanced"]

def test_counts_balance():
    assert reconcile_counts(10, 7, 2, 1)["balanced"]

def test_content_run_id_stable():
    assert run_id(b"x") == run_id(b"x")

def test_manifest_uses_full_sha():
    assert len(build_manifest(b"x", 1, 0)["input_sha256"]) == 64

def test_idempotent_record(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATABASE_PATH", tmp_path / "db.sqlite")
    manifest = build_manifest(b"x", 1, 0)
    assert store.record_run(manifest) and not store.record_run(manifest) and store.run_count() == 1  # TRAP-26

def test_difference_export_has_evidence():
    text = differences_csv([{"business_key": "A|0.13", "line_no": 8, "reason_code": "UNINVOICED", "amount_cny": "20.00"}])
    assert "reason_code" in text and "UNINVOICED" in text

