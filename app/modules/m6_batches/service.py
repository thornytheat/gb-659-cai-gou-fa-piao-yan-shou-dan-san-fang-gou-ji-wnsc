from app.manifest import build_manifest
from app.store import record_run
from .compare import reconcile_amounts

def run(payload: bytes = b"procurematch-sample") -> dict:
    account = reconcile_amounts("2260.00", "2034.00", "226.00", "0.00")
    manifest = build_manifest(payload, 34, 2)
    manifest["created"] = record_run(manifest)
    return {**manifest, **account}

def demo():
    return run()

