"""
@file test_layout_mirroring.py
@description 3D 미러링 비대면 상담 세션 생성 (LayoutMirroringUseCase) 및 멀티테넌시 파사드 권한 검증 단위 테스트
"""

from unittest.mock import MagicMock, patch

import pytest

from src.kpi_b2b.b2b_procurement.application.layout_mirroring_usecase import (
    LayoutMirroringUseCase,
)
from src.kpi_b2b.b2b_procurement.domain.expert_session import ExpertSessionStatusEnum
from src.kpi_b2b.facades.procurement_command_facade import ProcurementCommandFacadeImpl
from src.shared.enums.audit_severity_enum import AuditSeverityEnum
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.security.user_context import UserContext


@pytest.fixture
def mock_mysql_repo():
    """DB 영속화 (BaseRepositoryAdapter) 모킹"""
    return MagicMock()


@pytest.fixture
def mock_dependencies():
    """파사드 주입용 미사용 의존성 모킹"""
    return {
        "generate_quote_uc": MagicMock(),
        "redis_adapter": MagicMock(),
        "baseline_repo": MagicMock(),
    }


@pytest.fixture
def target_system(mock_mysql_repo, mock_dependencies):
    """테스트 대상 시스템(Facade & UseCase) 셋업 및 전역 로거 패치"""
    with (
        patch(
            "src.kpi_b2b.b2b_procurement.application.layout_mirroring_usecase.GlobalSystemLogger"
        ),
        patch("src.kpi_b2b.facades.procurement_command_facade.GlobalSystemLogger"),
        patch(
            "src.kpi_b2b.facades.procurement_command_facade.AuditLogger"
        ) as MockAuditLogger,
    ):
        mock_audit_logger_instance = MockAuditLogger.return_value

        # UseCase 인스턴스화
        mirroring_uc = LayoutMirroringUseCase(mysql_repo=mock_mysql_repo)

        # Facade 인스턴스화
        facade = ProcurementCommandFacadeImpl(
            generate_quote_uc=mock_dependencies["generate_quote_uc"],
            mirroring_uc=mirroring_uc,
            redis_adapter=mock_dependencies["redis_adapter"],
            baseline_repo=mock_dependencies["baseline_repo"],
        )

        yield facade, mock_mysql_repo, mock_audit_logger_instance


class TestLayoutMirroring:
    @pytest.fixture
    def valid_ctx(self):
        """정상적인 권한을 가진 UserContext 픽스처"""
        return UserContext(
            user_id="USR-200",
            username="factory_manager_b",
            company_id="TENANT_B",
            role=UserRoleEnum.FACTORY_MANAGER,
        )

    def test_create_expert_session_happy_path(self, target_system, valid_ctx):
        """TC-정상 (Happy Path): 권한이 일치할 때 도면 유출 방지용 1회성 토큰 발급 및 세션 생성 검증"""
        facade, mock_db, _ = target_system
        baseline_id = "BASELINE-3D-001"

        # When
        result_dto = facade.create_expert_session(
            baseline_id=baseline_id, ctx=valid_ctx
        )

        # Then
        # 1. DB 영속화 호출 여부 및 엔티티 상태 검증
        mock_db.save.assert_called_once()
        saved_entity = mock_db.save.call_args[0][0]

        assert saved_entity.baseline_id == baseline_id
        assert saved_entity.expert_id == "UNASSIGNED"
        assert saved_entity.status == ExpertSessionStatusEnum.WAITING
        assert saved_entity.session_token.startswith("TKN-")

        # 2. 응답 DTO 검증 (14400초 만료 시간 포함)
        assert result_dto.session_id.startswith("SESS-")
        assert result_dto.session_token == saved_entity.session_token
        assert result_dto.status == ExpertSessionStatusEnum.WAITING.value
        assert result_dto.expires_in_seconds == 14400

    def test_create_expert_session_isolation_violation(self, target_system):
        """TC-예외 (Edge Case): 멀티테넌시 권한 불일치 시 403 에러 발생 및 보안 감사 로그 검증"""
        facade, mock_db, mock_audit_logger = target_system

        # Given: "UNAUTHORIZED"가 포함된 company_id로 위반 모사
        invalid_ctx = UserContext(
            user_id="USR-HACKER",
            username="unauthorized_user",
            company_id="UNAUTHORIZED_TENANT",
            role=UserRoleEnum.CREATOR,
        )
        baseline_id = "BASELINE-SECRET-001"

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            facade.create_expert_session(baseline_id=baseline_id, ctx=invalid_ctx)

        # 예외 코드 및 상태 검증
        assert exc_info.value.error_code == "ERR_KPI_ISOLATION_VIOLATION"
        assert exc_info.value.status_code == 403

        # DB 저장 차단 검증
        mock_db.save.assert_not_called()

        # CRITICAL 감사 로깅 작동 검증
        mock_audit_logger.log_security_event.assert_called_once()
        audit_event = mock_audit_logger.log_security_event.call_args[0][0]
        assert audit_event.severity == AuditSeverityEnum.CRITICAL
        assert audit_event.action == "EXPERT_SESSION_ISOLATION_VIOLATION"

    def test_create_expert_session_db_failure(self, target_system, valid_ctx):
        """TC-에러 (Error Handling): DB 영속화 실패 시 500 내부 서버 에러로 안전하게 마스킹되는지 검증"""
        facade, mock_db, _ = target_system
        baseline_id = "BASELINE-ERROR-001"

        # Given: DB 저장 중 인프라 예외 발생 모사
        mock_db.save.side_effect = Exception(
            "pymysql.err.OperationalError: Connection lost"
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            facade.create_expert_session(baseline_id=baseline_id, ctx=valid_ctx)

        # 인프라 에러가 마스킹되어 전역 내부 에러로 변환되었는지 검증
        assert exc_info.value.error_code == "ERR_COMMON_INTERNAL_ERROR"
        assert exc_info.value.status_code == 500
        assert "시스템 내부 장애가 발생했습니다" in exc_info.value.message
