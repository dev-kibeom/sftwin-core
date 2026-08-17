from unittest.mock import MagicMock

import pytest
from kpi_b2b.facades.kpi_query_facade import KpiQueryFacade
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_dto import (
    GenerateDualKpiReportRequestDto,
)
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_usecase import (
    GenerateDualKpiReportUseCase,
)
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="USR-100",
        username="manager",
        company_id="TENANT_A",
        role=UserRoleEnum.FACTORY_MANAGER,
    )


@pytest.fixture
def dual_kpi_usecase():
    return GenerateDualKpiReportUseCase()


@pytest.fixture
def kpi_facade(dual_kpi_usecase):
    mock_calc_uc = MagicMock()
    mock_rbac = MagicMock()
    return KpiQueryFacade(
        calculate_kpi_uc=mock_calc_uc,
        dual_kpi_uc=dual_kpi_usecase,
        rbac_manager=mock_rbac,
    )


# TC-KPI-01: Happy Path - DTO를 통한 듀얼 KPI 및 ROI 리포트 생성 검증
def test_generate_dual_kpi_report_happy_path(kpi_facade, valid_ctx):
    req_dto = GenerateDualKpiReportRequestDto(
        baseline_oee=0.70,
        improved_oee=0.84,
        baseline_fpy=0.90,
        improved_fpy=0.95,
        turnkey_quote_cost=300000000.0,
    )

    report = kpi_facade.generate_dual_kpi_report(request_dto=req_dto, ctx=valid_ctx)

    assert report.baseline_oee == 0.70
    assert report.improved_oee == 0.84
    assert report.oee_improvement_rate == 20.0
    assert report.payback_period_months == 15.0
    assert report.investment_cost_krw == 300000000.0


# TC-KPI-02: Edge Case - OEE 입력값이 1.0 초과 시 ERR_COMMON_INVALID_INPUT 예외 변환 검증
def test_generate_dual_kpi_report_invalid_oee_value(kpi_facade, valid_ctx):
    req_dto = GenerateDualKpiReportRequestDto(
        baseline_oee=1.5,  # Invalid (1.0 초과)
        improved_oee=0.84,
        baseline_fpy=0.90,
        improved_fpy=0.95,
        turnkey_quote_cost=300000000.0,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        kpi_facade.generate_dual_kpi_report(request_dto=req_dto, ctx=valid_ctx)

    assert exc_info.value.error_code == GlobalErrorCodeEnum.ERR_COMMON_INVALID_INPUT
    assert exc_info.value.status_code == 400
