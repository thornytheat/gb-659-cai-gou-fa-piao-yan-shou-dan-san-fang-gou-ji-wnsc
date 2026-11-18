from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.web import page
from .service import demo

router = APIRouter()
ROWS = [{"key":"IV-001","status":"相等","value":"1130.00"},{"key":"IV-002","status":"尾差","value":"0.01"},{"key":"IV-003","status":"隔离","value":"13%"}]

@router.get("/tax", response_class=HTMLResponse)
def view(request: Request):
    return page(request, "m4.html", "税额核验", "/api/tax/check", ROWS)

@router.post("/api/tax/check")
def execute():
    return demo()

