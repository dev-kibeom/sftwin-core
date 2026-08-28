# File: plugins/fast_api/app.py
import os
import threading
from contextlib import asynccontextmanager

import rclpy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rclpy.executors import MultiThreadedExecutor

from plugins.fast_api.adapters.ros2_edge_client import Ros2EdgeServiceClient
from plugins.fast_api.adapters.ros2_webrtc_client import Ros2WebRtcSignalingClient
from plugins.fast_api.dependencies import clients
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 테스트 환경(TESTING=1)이거나 이미 DI Override가 설정된 경우 ROS2 백그라운드 스레드 기동 스킵
    is_testing = os.getenv("TESTING", "0") == "1" or bool(app.dependency_overrides)

    ros_node = None
    executor = None
    spin_thread = None

    if not is_testing:
        if not rclpy.ok():
            rclpy.init()
        ros_node = rclpy.create_node("fastapi_inbound_gateway")
        executor = MultiThreadedExecutor()
        executor.add_node(ros_node)

        spin_thread = threading.Thread(target=executor.spin, daemon=True)
        spin_thread.start()

        if clients.get_ros2_edge_service_client not in app.dependency_overrides:
            app.dependency_overrides[clients.get_ros2_edge_service_client] = lambda: (
                Ros2EdgeServiceClient(node=ros_node)
            )

        if clients.get_ros2_webrtc_signaling_client not in app.dependency_overrides:
            app.dependency_overrides[clients.get_ros2_webrtc_signaling_client] = (
                lambda: Ros2WebRtcSignalingClient(node=ros_node)
            )

    yield

    # 종료 처리
    if executor and ros_node:
        try:
            executor.shutdown()
            ros_node.destroy_node()
        except Exception:
            pass


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 Composition Root 팩토리"""
    app = FastAPI(
        title="Smart Factory Twin REST & Signaling API Plugin",
        description="FastAPI Inbound Adapter for ROS 2 Digital Twin & Simulation System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 미들웨어 체인 등록
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # 전역 예외 처리기 등록
    register_exception_handlers(app)

    # 도메인 API 라우터 등록
    api_v1_prefix = "/api/v1"
    app.include_router(asset_router, prefix=api_v1_prefix)
    app.include_router(digital_twin_router, prefix=api_v1_prefix)
    app.include_router(simulation_router, prefix=api_v1_prefix)
    app.include_router(edge_router, prefix=api_v1_prefix)
    app.include_router(webrtc_router, prefix=api_v1_prefix)

    @app.get("/health", tags=["Health"], summary="시스템 헬스체크")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": "1.0.0"}

    return app
