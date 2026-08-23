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
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="USR-100",
        username="manager",
        company_id="TENANT_A",
        role=UserRole.FACTORY_MANAGER,
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


def test_generate_dual_kpi_report_invalid_oee_value(kpi_facade, valid_ctx):
    req_dto = GenerateDualKpiReportRequestDto(
        baseline_oee=1.5,
        improved_oee=0.84,
        baseline_fpy=0.90,
        improved_fpy=0.95,
        turnkey_quote_cost=300000000.0,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        kpi_facade.generate_dual_kpi_report(request_dto=req_dto, ctx=valid_ctx)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert exc_info.value.status_code == 400
