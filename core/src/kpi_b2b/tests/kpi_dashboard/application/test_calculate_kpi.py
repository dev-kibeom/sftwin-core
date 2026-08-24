from unittest.mock import MagicMock

import pytest
from kpi_b2b.contracts.dtos.kpi_report_dto import KpiReportDto
from kpi_b2b.contracts.dtos.telemetry_summary_dto import TelemetrySummaryDto
from kpi_b2b.contracts.ports.outbound.i_telemetry_query_repository import (
    ITelemetryQueryRepository,
)
from kpi_b2b.kpi_dashboard.application.calculate_kpi.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole


@pytest.fixture
def mock_query_repo() -> MagicMock:
    return MagicMock(spec=ITelemetryQueryRepository)


@pytest.fixture
def usecase(mock_query_repo: MagicMock) -> CalculateKpiUseCase:
    return CalculateKpiUseCase(query_repo=mock_query_repo)


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


def test_tc_happy_path_calculate_kpi(
    usecase: CalculateKpiUseCase,
    mock_query_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 계측 통계 요약 조회 후 OEE/TEEP/FPY 산출 검증"""
    mock_query_repo.get_telemetry_summary_by_sim_id.return_value = TelemetrySummaryDto(
        sim_id="SIM-100",
        uptime_seconds=3600.0,
        total_time_seconds=4000.0,  # A = 0.9
        ideal_cycle_time=10.0,
        actual_cycle_time=10.0,  # P = 1.0
        good_count=95,
        total_count=100,  # Q = 0.95
    )

    result = usecase.execute(sim_id="SIM-100", ctx=standard_context)

    mock_query_repo.get_telemetry_summary_by_sim_id.assert_called_once_with(
        sim_id="SIM-100",
        company_id="TEST-COMPANY-01",
    )
    assert isinstance(result, KpiReportDto)
    assert result.oee == 0.855  # 0.9 * 1.0 * 0.95 = 0.855
    assert result.fpy == 0.95
    assert result.teep == round(0.855 * 0.85, 4)


def test_tc_edge_case_telemetry_not_found_or_unauthorized(
    usecase: CalculateKpiUseCase,
    mock_query_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-예외] 시뮬레이션 계측 데이터가 없거나 타 테넌트일 때 ERR_KPI_SIM_NOT_FOUND 검증"""
    mock_query_repo.get_telemetry_summary_by_sim_id.return_value = None

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(sim_id="INVALID-SIM", ctx=standard_context)

    mock_query_repo.get_telemetry_summary_by_sim_id.assert_called_once_with(
        sim_id="INVALID-SIM",
        company_id="TEST-COMPANY-01",
    )
    assert exc_info.value.error_code == GlobalErrorCode.ERR_KPI_SIM_NOT_FOUND
