from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.web import page
from .service import demo

router = APIRouter()
ROWS = [{"key":"SKU-A|13%","status":"2 对 1","value":"1130.00"},{"key":"SKU-B|9%","status":"1 对 2","value":"545.00"},{"key":"SKU-C|13%","status":"未匹配","value":"226.00"}]

@router.get("/matching", response_class=HTMLResponse)
def view(request: Request):
    return page(request, "m5.html", "多对多匹配", "/api/matches/solve", ROWS)

@router.post("/api/matches/solve")
def execute():
    return demo()

