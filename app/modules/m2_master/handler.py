from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.web import page
from .service import demo

router = APIRouter()
ROWS = [{"key":"000142","status":"已映射","value":"SKU-A"},{"key":"000143","status":"别名","value":"SKU-B"},{"key":"000144","status":"隔离","value":"—"}]

@router.get("/master", response_class=HTMLResponse)
def view(request: Request):
    return page(request, "m2.html", "主数据映射", "/api/master/resolve", ROWS)

@router.post("/api/master/resolve")
def execute():
    return demo()

