from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.kpi_b2b.b2b_procurement.adapters.inbound import procurement_router
from src.kpi_b2b.kpi_dashboard.adapters.inbound import kpi_router
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.global_exception_handler import GlobalExceptionHandler

app = FastAPI(title="KPI & B2B Service", version="1.0.0")

exception_handler = GlobalExceptionHandler()


@app.exception_handler(BaseSystemException)
async def base_system_exception_handler(request: Request, exc: BaseSystemException):
    dto, status_code = exception_handler.handle_base_system_exception(exc)
    return JSONResponse(status_code=status_code, content=dto.__dict__)


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    dto, status_code = exception_handler.handle_unexpected_exception(exc)
    return JSONResponse(status_code=status_code, content=dto.__dict__)


app.include_router(kpi_router.router)
app.include_router(procurement_router.router)


@app.get("/healthz")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
