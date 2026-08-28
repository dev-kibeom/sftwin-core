# File: plugins/fast_api/routers/__init__.py
from plugins.fast_api.routers.asset_router import router as asset_router
from plugins.fast_api.routers.digital_twin_router import (
    router as digital_twin_router,
)
from plugins.fast_api.routers.edge_router import router as edge_router
from plugins.fast_api.routers.simulation_router import (
    router as simulation_router,
)
from plugins.fast_api.routers.webrtc_router import router as webrtc_router

__all__ = [
    "asset_router",
    "digital_twin_router",
    "simulation_router",
    "edge_router",
    "webrtc_router",
]
