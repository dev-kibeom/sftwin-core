import logging

from fastapi import APIRouter

from src.shared.adapters.system_config_repository_adapter import (
    SystemConfigRepositoryAdapter,
)
from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.dtos.system_config_dto import SystemConfigDto
from src.shared.security.user_context import UserContext
from src.shared.services.system_config_service import SystemConfigService

logger = logging.getLogger("sftwin.shared.controllers.system_config")

router = APIRouter(prefix="/api/v1/shared/configs", tags=["System Config API"])


class SystemConfigController:
    """GET /api/v1/shared/configs/{config_key} 엔드포인트 컨트롤러"""

    def __init__(self, service: SystemConfigService | None = None):
        if not service:
            adapter = SystemConfigRepositoryAdapter()
            service = SystemConfigService(repository=adapter)
        self.service = service

    def get_config_by_key(
        self,
        config_key: str,
        user_ctx: UserContext,
    ) -> GlobalResponseDto[SystemConfigDto]:
        """공통 시스템 설정 단건 조회"""
        logger.info(
            f"[SystemConfigController] Config query request: key={config_key}, "
            f"user_id={user_ctx.user_id if user_ctx else 'UNKNOWN'}"
        )

        config_dto = self.service.get_config(config_key)

        return GlobalResponseDto.success_response(
            data=config_dto,
            message="System configuration retrieved successfully.",
        )
