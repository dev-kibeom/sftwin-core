# File: plugins/fast_api/routers/__init__.py
from plugins.fast_api.routers.asset_router import router as asset_router
from plugins.fast_api.routers.digital_twin_router import (
    router as digital_twin_router,
)

__all__ = ["asset_router", "digital_twin_router"]
