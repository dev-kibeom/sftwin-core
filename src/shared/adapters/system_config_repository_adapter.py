import logging
from datetime import datetime, timezone

from src.shared.ports.system_config_repository import (
    SystemConfigEntity,
    SystemConfigRepository,
)

logger = logging.getLogger("sftwin.shared.adapters.system_config_repo")


class BaseRepositoryAdapter:
    """공통 데이터베이스 접근 베이스 어댑터"""

    def __init__(self, db_session: object | None = None):
        self.db_session = db_session


class SystemConfigRepositoryAdapter(BaseRepositoryAdapter, SystemConfigRepository):
    """공통 시스템 설정 레포지토리 어댑터 (SystemConfigRepository 인터페이스 구현)"""

    def __init__(self, db_session: object | None = None):
        super().__init__(db_session)
        # 개발/PoC/시드 데이터베이스 인메모리 스토리지 (GTS v2.0 5.2절 seed_global_config)
        self._configs: dict[str, SystemConfigEntity] = {
            "EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS": SystemConfigEntity(
                config_key="EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS",
                config_value="100",
                description="에지 관제 엔진 Heartbeat 단절 판단 타임아웃 (ms)",
                updated_at=datetime.now(timezone.utc).isoformat(),
                is_deleted=0,
            ),
            "MAX_SIM_CONCURRENT_USERS": SystemConfigEntity(
                config_key="MAX_SIM_CONCURRENT_USERS",
                config_value="50",
                description="60fps WebGL 시뮬레이션 엔진 최대 동시 접속자 수",
                updated_at=datetime.now(timezone.utc).isoformat(),
                is_deleted=0,
            ),
            "DELETED_CONFIG_KEY": SystemConfigEntity(
                config_key="DELETED_CONFIG_KEY",
                config_value="0",
                description="삭제된 테스트 설정 키",
                updated_at=datetime.now(timezone.utc).isoformat(),
                is_deleted=1,  # Soft Deleted
            ),
        }

    def find_by_key(self, config_key: str) -> SystemConfigEntity | None:
        """system_configs 테이블 조회 및 is_deleted=0 항목 필터링"""
        logger.info(
            f"[SystemConfigRepositoryAdapter] Querying system_configs for key={config_key}"
        )
        entity = self._configs.get(config_key)

        if not entity or entity.is_deleted == 1:
            logger.warning(
                f"[SystemConfigRepositoryAdapter] Config key not found or deleted: key={config_key}"
            )
            return None

        return entity
