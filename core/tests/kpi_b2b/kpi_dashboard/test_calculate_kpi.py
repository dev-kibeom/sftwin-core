"""
@file test_calculate_kpi.py
@description 표준 제조 KPI 연산(CalculateKpiUseCase) 및 파사드 단위 테스트 (언패킹 및 RBAC 연동 픽스)
"""

from unittest.mock import MagicMock, patch

import pytest
from kpi_b2b.facades.kpi_query_facade import KpiQueryFacadeImpl
from kpi_b2b.kpi_dashboard.application.calculate_kpi.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from kpi_b2b.kpi_dashboard.ports.outbound.base_time_series_port import (
    BaseTimeSeriesPort,
)
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.security.user_context import UserContext


@pytest.fixture
def mock_ts_adapter():
    return MagicMock(spec=BaseTimeSeriesPort)


@pytest.fixture
def mock_rbac_manager():
    return MagicMock()


@pytest.fixture
def mock_sim_repo():
    return MagicMock()


@pytest.fixture
def target_system(mock_ts_adapter, mock_rbac_manager, mock_sim_repo):
    with patch(
        "kpi_b2b.kpi_dashboard.application.calculate_kpi.calculate_kpi_usecase.GlobalSystemLogger"
    ):
        usecase = CalculateKpiUseCase(ts_adapter=mock_ts_adapter)
        facade = KpiQueryFacadeImpl(
            calculate_kpi_uc=usecase,
            rbac_manager=mock_rbac_manager,
            sim_repo=mock_sim_repo,
        )
        # 4개의 객체를 정확히 yield
        yield facade, mock_ts_adapter, mock_rbac_manager, mock_sim_repo


class TestCalculateKpi:
    def test_calculate_oee_happy_path(self, target_system):
        # 4개 변수 언패킹으로 ValueError 해결
        facade, mock_ts_adapter, mock_rbac, mock_repo = target_system

        valid_ctx = UserContext(
            user_id="USR-001",
            username="test_manager",
            company_id="TENANT_A",
            role=UserRoleEnum.FACTORY_MANAGER,
        )
        sim_id = "SIM-20231010-01"

        mock_repo.get_owner.return_value = "TENANT_A"
        mock_rbac.validate_company_isolation.return_value = True

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

        result_dto = facade.calculate_oee(sim_id=sim_id, ctx=valid_ctx)

        mock_rbac.validate_company_isolation.assert_called_once()
        assert result_dto is not None
        assert round(result_dto.oee, 2) == 0.70

    def test_calculate_oee_isolation_violation(self, target_system):
        facade, _, mock_rbac, mock_repo = target_system

        invalid_ctx = UserContext(
            user_id="USR-HACKER",
            username="hacker",
            company_id="HACKER_TENANT",
            role=UserRoleEnum.CREATOR,
        )
        sim_id = "SIM-SECRET-01"

        mock_repo.get_owner.return_value = "TARGET_TENANT"
        mock_rbac.validate_company_isolation.side_effect = BaseSystemException(
            error_code=GlobalErrorCodes.ERR_SHARED_FORBIDDEN,
            message="Access denied",
            status_code=403,
        )

        with pytest.raises(BaseSystemException) as exc_info:
            facade.calculate_oee(sim_id=sim_id, ctx=invalid_ctx)

        assert exc_info.value.status_code == 403

    def test_calculate_oee_sim_not_found(self, target_system):
        facade, mock_ts_adapter, mock_rbac, mock_repo = target_system
        valid_ctx = UserContext(
            user_id="USR-001",
            username="mgr",
            company_id="TENANT_A",
            role=UserRoleEnum.FACTORY_MANAGER,
        )
        mock_repo.get_owner.return_value = "TENANT_A"
        mock_rbac.validate_company_isolation.return_value = True
        mock_ts_adapter.fetch_simulation_logs.return_value = []

        with pytest.raises(BaseSystemException) as exc_info:
            facade.calculate_oee(sim_id="SIM-EMPTY", ctx=valid_ctx)
        assert exc_info.value.error_code == GlobalErrorCodes.ERR_KPI_SIM_NOT_FOUND

    def test_calculate_oee_db_timeout(self, target_system):
        facade, mock_ts_adapter, mock_rbac, mock_repo = target_system
        valid_ctx = UserContext(
            user_id="USR-001",
            username="mgr",
            company_id="TENANT_A",
            role=UserRoleEnum.FACTORY_MANAGER,
        )
        mock_repo.get_owner.return_value = "TENANT_A"
        mock_rbac.validate_company_isolation.return_value = True
        mock_ts_adapter.fetch_simulation_logs.side_effect = Exception("Timeout")

        with pytest.raises(BaseSystemException) as exc_info:
            facade.calculate_oee(sim_id="SIM-TIMEOUT", ctx=valid_ctx)
        assert exc_info.value.error_code == GlobalErrorCodes.ERR_KPI_DB_TIMEOUT
