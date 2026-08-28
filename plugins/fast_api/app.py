from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from plugins.fast_api.middlewares.correlation_id_middleware import (
    CorrelationIdMiddleware,
)
from plugins.fast_api.middlewares.exception_handler import (
    register_exception_handlers,
)
from plugins.fast_api.middlewares.request_logging_middleware import (
    RequestLoggingMiddleware,
)

from plugins.fast_api.routers.asset_router import router as asset_router
from plugins.fast_api.routers.digital_twin_router import (
    router as digital_twin_router,
)
from plugins.fast_api.routers.edge_router import router as edge_router
from plugins.fast_api.routers.simulation_router import (
    router as simulation_router,
)
from plugins.fast_api.routers.webrtc_router import router as webrtc_router


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 Composition Root 팩토리"""
    app = FastAPI(
        title="Smart Factory Twin REST & Signaling API Plugin",
        description="FastAPI Inbound Adapter for ROS 2 Digital Twin & Simulation System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 1. CORS 미들웨어 등록
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. 커스텀 미들웨어 체인 등록 (요청 유입 역순 등록 / 실행 순서: CorrelationId -> RequestLogging)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # 3. 전역 예외 처리기 등록 (표준 GlobalResponseDto Envelope 변환)
    register_exception_handlers(app)

    # 4. 도메인 API 라우터 등록
    api_v1_prefix = "/api/v1"
    app.include_router(asset_router, prefix=api_v1_prefix)
    app.include_router(digital_twin_router, prefix=api_v1_prefix)
    app.include_router(simulation_router, prefix=api_v1_prefix)
    app.include_router(edge_router, prefix=api_v1_prefix)
    app.include_router(webrtc_router, prefix=api_v1_prefix)

    # 5. 시스템 헬스체크 엔드포인트
    @app.get("/health", tags=["Health"], summary="시스템 헬스체크")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": "1.0.0"}

    return app
