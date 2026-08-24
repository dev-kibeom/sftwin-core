import uuid

from kpi_b2b.b2b_procurement.domain.expert_session.expert_session import (
    ExpertSession,
)
from kpi_b2b.ports.inbound.dtos.session_data_dto import SessionDataDto
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.ports.outbound.i_procurement_query_repository import (
    IProcurementQueryRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class CreateExpertSessionUseCase:
    """전문가 매칭 및 협업 세션을 생성하는 유스케이스"""

    def __init__(
        self,
        command_repo: IProcurementCommandRepository,
        query_repo: IProcurementQueryRepository,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._command_repo = command_repo
        self._query_repo = query_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="CreateExpertSessionUseCase"
        )

    @require_user_context
    def execute(self, baseline_id: str, ctx: UserContext) -> SessionDataDto:
        # 1. 대상 베이스라인 조회 및 테넌시 소유권 검증 (IDOR 방어: 404 단일화)
        owner_id = self._query_repo.get_baseline_owner(baseline_id)
        if not owner_id or owner_id != ctx.company_id:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_NOT_FOUND,
                custom_message=f"Digital twin baseline '{baseline_id}' does not exist or access is forbidden.",
            )

        # 2. 도메인 세션 엔티티 생성 및 불변식 검증
        try:
            session_entity = ExpertSession(
                session_id=f"SESS-{uuid.uuid4()}",
                baseline_id=baseline_id,
                session_token=f"TKN-{uuid.uuid4().hex}",
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        # 3. 저장소 영속화 (DB 장애 시 Repository Adapter가 BaseSystemException을 직접 전파)
        self._command_repo.save_expert_session(session_entity)

        # 4. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Successfully created expert session: {session_entity.session_id}",
            extra={
                "session_id": session_entity.session_id,
                "baseline_id": baseline_id,
            },
        )

        return SessionDataDto(
            session_id=session_entity.session_id,
            session_token=session_entity.session_token,
            status=session_entity.status.value,
            expires_in_seconds=session_entity.expires_in_seconds,
        )
