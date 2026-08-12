"""
===============================================================================
[File Name] main.py
[Location ] /src/kpi_b2b/main.py
[Description]
 - KPI & B2B 서비스 전용 FastAPI 메인 엔트리포인트입니다.
===============================================================================
"""

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.kpi_b2b.b2b_procurement.adapters.inbound import procurement_router
from src.kpi_b2b.kpi_dashboard.adapters.inbound import kpi_router
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.global_exception_handler import GlobalExceptionHandler

app = FastAPI(title="KPI & B2B Service", version="1.0.0")

# CORS Middleware (웹 UI 및 외부 B2B 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

exception_handler = GlobalExceptionHandler()


@app.exception_handler(BaseSystemException)
async def base_system_exception_handler(request: Request, exc: BaseSystemException):
    dto, status_code = exception_handler.handle_base_system_exception(exc)
    return JSONResponse(status_code=status_code, content=dto.__dict__)


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    dto, status_code = exception_handler.handle_unexpected_exception(exc)
    return JSONResponse(status_code=status_code, content=dto.__dict__)


# 1. 확장이 완료된 라우터 바인딩
app.include_router(kpi_router.router)
app.include_router(procurement_router.router)


# 2. GTS 5.4 규약 헬스체크 엔드포인트
@app.get("/healthz", tags=["System"])
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/kpi-b2b/healthz", tags=["System"])
async def api_health_check():
    return {
        "status": "ok",
        "service": "kpi_b2b",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
