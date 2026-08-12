"""
@file layout_mirroring_usecase.py
@description 상담 세션 엔티티 생성 및 DB 영속화, 인프라 에러 마스킹을 제어하는 유즈케이스
"""

from typing import Any

from src.kpi_b2b.b2b_procurement.application.layout_mirroring.session_data_dto import (
    SessionDataDto,
)
from src.kpi_b2b.b2b_procurement.domain.expert_session import ExpertSession
from src.shared.dtos.log_dtos import LogContext
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.logger.global_system_logger import GlobalSystemLogger


class LayoutMirroringUseCase:
    def __init__(
        self,
        mysql_repo: Any,
        logger: GlobalSystemLogger | None = None,
    ):
        self._mysql_repo = mysql_repo
        self._logger = logger or GlobalSystemLogger(
            component_name="LayoutMirroring_UseCase"
        )

    def execute(self, baseline_id: str, company_id: str) -> SessionDataDto:
        log_ctx = LogContext(
            context={"baseline_id": baseline_id, "company_id": company_id}
        )
        self._logger.info(
            "Initiating secure 3D mirroring expert session creation.", log_ctx
        )

        session_entity = ExpertSession.create_new_session(baseline_id=baseline_id)

        try:
            if self._mysql_repo:
                self._mysql_repo.save(session_entity)
        except Exception as e:
            log_ctx.exc = e
            self._logger.error(
                "Database persistence failed during expert session creation.", log_ctx
            )
            raise BaseSystemException(
                error_code="ERR_COMMON_INTERNAL_ERROR",
                message="시스템 내부 장애가 발생했습니다. 잠시 후 다시 시도해주세요.",
                status_code=500,
            )

        self._logger.info(
            f"Successfully generated expert session: {session_entity.session_id}",
            log_ctx,
        )

        return SessionDataDto(
            session_id=session_entity.session_id,
            session_token=session_entity.session_token,
            status=session_entity.status.value,
            expires_in_seconds=14400,
        )
