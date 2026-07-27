import logging

from src.shared.dtos.system_config_dto import SystemConfigDto
from src.shared.exceptions.base_exception import ConfigNotFoundException
from src.shared.ports.system_config_repository import SystemConfigRepository

logger = logging.getLogger("sftwin.shared.services.system_config")


class SystemConfigService:
    """공통 시스템 설정 조회 비즈니스 및 DTO 매핑 서비스 (Clean Architecture)"""

    def __init__(self, repository: SystemConfigRepository):
        self.repository = repository

    def get_config(self, config_key: str) -> SystemConfigDto:
        """설정 키 단건 조회 및 ConfigNotFoundException 예외 처리"""
        if not config_key:
            logger.warning("[SystemConfigService] Config key is empty.")
            raise ConfigNotFoundException(
                message="Requested system configuration key cannot be empty.",
                details={"config_key": config_key},
            )

        entity = self.repository.find_by_key(config_key)

        if not entity:
            logger.warning(f"[SystemConfigService] Config key not found: {config_key}")
            raise ConfigNotFoundException(
                message="Requested system configuration key does not exist.",
                details={"config_key": config_key},
            )

        logger.info(
            f"[SystemConfigService] Config successfully retrieved: {config_key}"
        )
        return SystemConfigDto(
            config_key=entity.config_key,
            config_value=entity.config_value,
            description=entity.description,
            updated_at=entity.updated_at,
        )
