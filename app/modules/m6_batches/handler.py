from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.web import page
from .service import demo

router = APIRouter()
ROWS = [{"key":"RUN-659-A","status":"守恒","value":"36"},{"key":"RUN-659-B","status":"复用","value":"36"},{"key":"RUN-659-C","status":"差异","value":"2"}]

@router.get("/batches", response_class=HTMLResponse)
def view(request: Request):
    return page(request, "m6.html", "差异批次", "/api/reconcile", ROWS)

@router.post("/api/reconcile")
def execute():
    return demo()

@router.get("/api/export/differences.csv")
def export_differences():
    from fastapi.responses import PlainTextResponse
    from .exporter import differences_csv
    body = differences_csv([{"business_key": "SKU-C|0.13", "line_no": 9, "reason_code": "UNINVOICED", "amount_cny": "226.00"}])
    return PlainTextResponse(body, media_type="text/csv", headers={"content-disposition": "attachment; filename=differences.csv"})

