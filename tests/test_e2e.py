from fastapi.testclient import TestClient
from app.main import app

def test_all_module_pages_accessible():
    client = TestClient(app)
    for path in ("/documents", "/master", "/quantity", "/tax", "/matching", "/batches"):
        response = client.get(path)
        assert response.status_code == 200 and "panel" in response.text

def test_full_sample_flow_has_exact_amounts():
    client = TestClient(app)
    results = [client.post(path).json() for path in ("/api/documents/import", "/api/master/resolve", "/api/quantity/match", "/api/tax/check", "/api/matches/solve", "/api/reconcile")]
    assert results[0]["amount"] == "1000.00" and results[3]["gross"] == "1130.00" and results[4]["amount"] == "1130.00"

def test_difference_export_downloads():
    response = TestClient(app).get("/api/export/differences.csv")
    assert response.status_code == 200 and "UNINVOICED" in response.text

