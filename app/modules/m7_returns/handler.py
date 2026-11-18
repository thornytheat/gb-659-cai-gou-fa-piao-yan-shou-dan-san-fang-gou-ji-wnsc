from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi import HTTPException

from app.web import page
from .service import (
    register_return, supplement_batch, get_return, list_returns,
)

router = APIRouter()
ROWS = [
    {"key": "RT-20261118-01", "status": "批号待补", "value": "10 件 / 130.00"},
    {"key": "LOT-20260901-07", "status": "批号补齐", "value": "+2 件 / +26.00"},
    {"key": "重跑同一笔", "status": "幂等复用", "value": "0.00"},
]

DOMAIN_ERROR_STATUS = {
    "UNKNOWN_SKU": 422, "BATCH_NOT_FOUND": 422,
    "PACK_CODE_NOT_REGISTERED": 422, "RETURN_EXCEEDS_RECEIPT": 422,
    "RETURN_NOT_FOUND": 404, "BATCH_PIECES_EXCEED_RETURN": 422,
    "BATCH_BOXES_MISMATCH": 422, "EMPTY_VALUE": 422,
    "NEGATIVE_QUANTITY": 422, "EMPTY_PACK_SPEC": 422,
}


def _domain_error(exc: ValueError) -> HTTPException:
    code = str(exc).strip("'")
    status = DOMAIN_ERROR_STATUS.get(code, 422)
    return HTTPException(status_code=status, detail={"code": code, "message": str(exc)})


@router.get("/returns", response_class=HTMLResponse)
def view(request: Request):
    return page(request, "m7.html", "退货红票", "/api/returns/register", ROWS)


@router.post("/api/returns/register")
def execute_register(payload: dict | None = None):
    try:
        return register_return(payload)
    except ValueError as exc:
        raise _domain_error(exc) from exc


@router.post("/api/returns/supplement")
def execute_supplement(payload: dict | None = None):
    try:
        return supplement_batch(payload)
    except ValueError as exc:
        raise _domain_error(exc) from exc


@router.get("/api/returns/{return_no}")
def execute_get(return_no: str):
    try:
        return get_return(return_no)
    except ValueError as exc:
        raise _domain_error(exc) from exc


@router.get("/api/returns")
def execute_list():
    return list_returns()
