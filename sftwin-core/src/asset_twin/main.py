from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.global_exception_handler import GlobalExceptionHandler

app = FastAPI(title="Asset & Digital Twin Service", version="1.0.0")

exception_handler = GlobalExceptionHandler()


@app.exception_handler(BaseSystemException)
async def base_system_exception_handler(request: Request, exc: BaseSystemException):
    dto, status_code = exception_handler.handle_base_system_exception(exc)
    return JSONResponse(status_code=status_code, content=dto.__dict__)


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    dto, status_code = exception_handler.handle_unexpected_exception(exc)
    return JSONResponse(status_code=status_code, content=dto.__dict__)


@app.get("/healthz")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/assets/healthz")
async def api_health_check():
    return {
        "status": "ok",
        "service": "asset_twin",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
