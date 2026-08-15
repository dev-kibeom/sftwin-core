"""
===============================================================================
[File Name] main.py
[Location ] /plugins/fast_api/main.py
[Description]
 - Smart Factory Digital Twin 전 서브도메인 통합 FastAPI 엔트리포인트입니다.
===============================================================================
"""

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.global_exception_handler import GlobalExceptionHandler

# Subdomain Routers
from plugins.fast_api.routers.asset_router import router as asset_router
from plugins.fast_api.routers.digital_twin_router import router as digital_twin_router
from plugins.fast_api.routers.edge_control_router import router as edge_control_router
from plugins.fast_api.routers.kpi_router import router as kpi_router
from plugins.fast_api.routers.procurement_router import router as procurement_router
from plugins.fast_api.routers.simulation_router import router as simulation_router

app = FastAPI(
    title="Smart Factory Digital Twin Platform API",
    version="1.0.0",
    description="Clean Architecture 기반 통합 제조 디지털 트윈 & FMS 시뮬레이션 플랫폼 백엔드",
)

# CORS Middleware
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


# ------------------------------------------------------------------------------
# All Subdomain Routers Mounting
# ------------------------------------------------------------------------------
app.include_router(asset_router)
app.include_router(digital_twin_router)
app.include_router(edge_control_router)
app.include_router(simulation_router)
app.include_router(kpi_router)
app.include_router(procurement_router)


# ------------------------------------------------------------------------------
# System Health Check Endpoint
# ------------------------------------------------------------------------------
@app.get("/healthz", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "service": "sftwin-fastapi-platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
