"""
===============================================================================
[File Name] main.py
[Location ] /src/asset_twin/main.py
[Description]
 - Asset & Digital Twin 서비스 전용 FastAPI 메인 엔트리포인트입니다.
===============================================================================
"""

from datetime import datetime, timezone

# 1. 신규 라우터 Import
from asset_twin.twin_reconstruction.adapters.inbound.asset_twin_router import (
    router as asset_twin_router,
)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.global_exception_handler import GlobalExceptionHandler

app = FastAPI(title="Asset & Digital Twin Service", version="1.0.0")

# CORS Middleware (웹 UI 3D Canvas 및 외부 통신용)
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


# 2. 신규 라우터 바인딩
app.include_router(asset_twin_router)


# 3. GTS 5.4 규약 헬스체크 엔드포인트
@app.get("/healthz", tags=["System"])
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/assets/healthz", tags=["System"])
async def api_health_check():
    return {
        "status": "ok",
        "service": "asset_twin",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
