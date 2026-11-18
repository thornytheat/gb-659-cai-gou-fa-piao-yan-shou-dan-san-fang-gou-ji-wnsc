from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.web import page
from .service import demo

router = APIRouter()
ROWS = [{"key":"SKU-A|13%","status":"未到","value":"2"},{"key":"SKU-B|9%","status":"相等","value":"8"},{"key":"SKU-C|13%","status":"退货","value":"1"}]

@router.get("/quantity", response_class=HTMLResponse)
def view(request: Request):
    return page(request, "m3.html", "数量勾稽", "/api/quantity/match", ROWS)

@router.post("/api/quantity/match")
def execute():
    return demo()

