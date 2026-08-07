"""
@file test_calculate_kpi.py
@description 표준 제조 KPI 연산(CalculateKpiUseCase) 및 파사드(KpiQueryFacadeImpl) 비즈니스 흐름 단위 테스트
"""

from unittest.mock import MagicMock, patch

import pytest

from src.kpi_b2b.facades.kpi_query_facade import KpiQueryFacadeImpl
from src.kpi_b2b.kpi_dashboard.adapters.base_time_series_port import BaseTimeSeriesPort
from src.kpi_b2b.kpi_dashboard.application.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from src.shared.enums.audit_severity_enum import AuditSeverityEnum
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.security.user_context import UserContext


@pytest.fixture
def mock_ts_adapter():
    """시계열 데이터 조회를 모방하는 외부 어댑터 Mocking"""
    return MagicMock(spec=BaseTimeSeriesPort)


@pytest.fixture
def target_system(mock_ts_adapter):
    """테스트 대상 시스템(Facade & UseCase) 셋업 및 공통 로거 Mocking"""
    with (
        patch(
            "src.kpi_b2b.kpi_dashboard.application.calculate_kpi_usecase.GlobalSystemLogger"
        ),
        patch("src.kpi_b2b.facades.kpi_query_facade.AuditLogger") as MockAuditLogger,
    ):
        mock_audit_logger_instance = MockAuditLogger.return_value
        usecase = CalculateKpiUseCase(ts_adapter=mock_ts_adapter)
        facade = KpiQueryFacadeImpl(calculate_kpi_uc=usecase)

        yield facade, mock_ts_adapter, mock_audit_logger_instance


class TestCalculateKpi:
    def test_calculate_oee_happy_path(self, target_system):
        """TC-정상 (Happy Path): 권한이 일치하고 정상적인 시계열 데이터가 반환되는 경우 지표 연산 성공 검증"""
        facade, mock_ts_adapter, _ = target_system

        # Given: GTS 3.5 필수 파라미터(role, username) 반영
        valid_ctx = UserContext(
            user_id="USR-001",
            username="test_manager",
            company_id="VALID_TENANT_A",
            role=UserRoleEnum.FACTORY_MANAGER,
        )
        sim_id = "SIM-20231010-01"

        # 시계열 로그 배열 Mock 데이터 셋업 (2개의 로그 레코드)
        mock_ts_adapter.fetch_simulation_logs.return_value = [
            {
                "uptime": 40.0,
                "total_time": 50.0,
                "ideal_cycle": 10.0,
                "actual_cycle": 12.0,
                "good_count": 48,
                "total_count": 50,
            },
            {
                "uptime": 45.0,
                "total_time": 50.0,
                "ideal_cycle": 10.0,
                "actual_cycle": 11.0,
                "good_count": 47,
                "total_count": 50,
            },
        ]

        # When
        result_dto = facade.calculate_oee(sim_id=sim_id, ctx=valid_ctx)

        # Then
        assert result_dto is not None
        assert result_dto.report_id.startswith("RPT-")

        # 수동 계산 검증 (OEE = 0.85 * 0.86956 * 0.95 = 0.7021...)
        assert round(result_dto.oee, 2) == 0.70
        assert round(result_dto.fpy, 2) == 0.95
        assert result_dto.estimated_roi_months == 18.5

    def test_calculate_oee_isolation_violation(self, target_system):
        """TC-예외 (Edge Case 2): 멀티테넌시 권한 위반 시 403 에러 발생 및 Audit Logging 검증"""
        facade, mock_ts_adapter, mock_audit_logger = target_system

        # Given
        invalid_ctx = UserContext(
            user_id="USR-HACKER",
            username="hacker_user",
            company_id="UNAUTHORIZED_TENANT",
            role=UserRoleEnum.CREATOR,
        )
        sim_id = "SIM-SECRET-01"

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            facade.calculate_oee(sim_id=sim_id, ctx=invalid_ctx)

        assert exc_info.value.error_code == "ERR_KPI_ISOLATION_VIOLATION"
        assert exc_info.value.status_code == 403

        # AuditLogger가 CRITICAL 수준으로 잘 기록했는지 확인
        mock_audit_logger.log_security_event.assert_called_once()
        called_args = mock_audit_logger.log_security_event.call_args[0][0]
        assert called_args.severity == AuditSeverityEnum.CRITICAL
        assert called_args.action == "ACCESS_DENIED_KPI_DASHBOARD"

    def test_calculate_oee_sim_not_found(self, target_system):
        """TC-예외 (Edge Case 1): 대상 시뮬레이션 로그가 존재하지 않을 때 404 에러 발생 검증"""
        facade, mock_ts_adapter, _ = target_system

        # Given
        valid_ctx = UserContext(
            user_id="USR-001",
            username="test_manager",
            company_id="VALID_TENANT_A",
            role=UserRoleEnum.FACTORY_MANAGER,
        )
        sim_id = "SIM-EMPTY-01"

        # 빈 배열 반환 (데이터 없음)
        mock_ts_adapter.fetch_simulation_logs.return_value = []

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            facade.calculate_oee(sim_id=sim_id, ctx=valid_ctx)

        assert exc_info.value.error_code == "ERR_KPI_SIM_NOT_FOUND"
        assert exc_info.value.status_code == 404

    def test_calculate_oee_db_timeout(self, target_system):
        """TC-에러 (Error Handling): InfluxDB 쿼리 타임아웃/예외 발생 시 500 마스킹 에러 발생 검증"""
        facade, mock_ts_adapter, _ = target_system

        # Given
        valid_ctx = UserContext(
            user_id="USR-001",
            username="test_manager",
            company_id="VALID_TENANT_A",
            role=UserRoleEnum.FACTORY_MANAGER,
        )
        sim_id = "SIM-TIMEOUT-01"

        # DB 연결 지연 등 원시 예외 발생 모사
        mock_ts_adapter.fetch_simulation_logs.side_effect = Exception(
            "ReadTimeoutError"
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            facade.calculate_oee(sim_id=sim_id, ctx=valid_ctx)

        assert exc_info.value.error_code == "ERR_KPI_DB_TIMEOUT"
        assert exc_info.value.status_code == 500
        assert "시간 초과 또는 내부 오류 발생" in exc_info.value.message
