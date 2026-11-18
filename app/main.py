from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import APP_VERSION
from app.store import init_db
from app.modules.m1_documents.handler import router as m1_documents_router
from app.modules.m2_master.handler import router as m2_master_router
from app.modules.m3_quantity.handler import router as m3_quantity_router
from app.modules.m4_tax.handler import router as m4_tax_router
from app.modules.m5_matching.handler import router as m5_matching_router
from app.modules.m6_batches.handler import router as m6_batches_router

app = FastAPI(title="采购三方勾稽报告", version=APP_VERSION)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.state.templates = Jinja2Templates(directory="app/templates")
app.state.version = APP_VERSION
app.include_router(m1_documents_router)
app.include_router(m2_master_router)
app.include_router(m3_quantity_router)
app.include_router(m4_tax_router)
app.include_router(m5_matching_router)
app.include_router(m6_batches_router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/documents")

@app.get("/api/health")
def health():
    return {"status": "ok", "version": APP_VERSION}

