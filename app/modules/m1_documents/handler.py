from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.web import page
from .service import demo

router = APIRouter()
ROWS = [{"key":"PO-001","status":"采购","value":"12"},{"key":"GR-001","status":"验收","value":"10"},{"key":"IV-001","status":"发票","value":"9"}]

@router.get("/documents", response_class=HTMLResponse)
def view(request: Request):
    return page(request, "m1.html", "单据采信", "/api/documents/import", ROWS)

@router.post("/api/documents/import")
def execute():
    return demo()

