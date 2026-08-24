import pytest
from kpi_b2b.contracts.dtos.dual_kpi_report_dto import DualKpiReportDto
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_dto import (
    GenerateDualKpiReportRequestDto,
)
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_usecase import (
    GenerateDualKpiReportUseCase,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole


@pytest.fixture
def usecase() -> GenerateDualKpiReportUseCase:
    return GenerateDualKpiReportUseCase()


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


def test_tc_happy_path_generate_dual_kpi_report(
    usecase: GenerateDualKpiReportUseCase,
    standard_context: UserContext,
):
    """[TC-정상] 요청 DTO를 바탕으로 Dual KPI 및 ROI 분석 보고서 정상 생성 검증"""
    req_dto = GenerateDualKpiReportRequestDto(
        baseline_oee=0.6,
        improved_oee=0.75,
        baseline_fpy=0.9,
        improved_fpy=0.95,
        turnkey_quote_cost=50_000_000.0,
    )

    result = usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert isinstance(result, DualKpiReportDto)
    assert result.baseline_oee == 0.6
    assert result.improved_oee == 0.75
    assert result.oee_improvement_rate == 25.0
    assert result.investment_cost_krw == 50_000_000.0
    assert result.payback_period_months > 0.0


def test_tc_edge_case_invalid_oee_input(
    usecase: GenerateDualKpiReportUseCase,
    standard_context: UserContext,
):
    """[TC-예외] 1.0을 초과하는 비정상 OEE 입력 시 ERR_COMMON_INVALID_INPUT(400) 발생 검증"""
    req_dto = GenerateDualKpiReportRequestDto(
        baseline_oee=1.5,
        improved_oee=0.8,
        baseline_fpy=0.9,
        improved_fpy=0.95,
        turnkey_quote_cost=50_000_000.0,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert exc_info.value.status_code == 400
