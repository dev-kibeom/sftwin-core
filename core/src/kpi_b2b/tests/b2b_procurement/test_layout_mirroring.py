from unittest.mock import MagicMock, patch

import pytest
from kpi_b2b.b2b_procurement.application.layout_mirroring.layout_mirroring_usecase import (
    LayoutMirroringUseCase,
)
from kpi_b2b.b2b_procurement.domain.enums.expert_session_status_enum import (
    ExpertSessionStatusEnum,
)
from kpi_b2b.facades.procurement_command_facade import ProcurementCommandFacade
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.ports.outbound.i_procurement_query_repository import (
    IProcurementQueryRepository,
)
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.security.rbac_authorization_manager import RbacAuthorizationManager


@pytest.fixture
def mock_command_repo():
    return MagicMock(spec=IProcurementCommandRepository)


@pytest.fixture
def mock_query_repo():
    return MagicMock(spec=IProcurementQueryRepository)


@pytest.fixture
def mock_gen_quote_uc():
    return MagicMock()


@pytest.fixture
def mock_prod_order_uc():
    return MagicMock()


@pytest.fixture
def mock_rbac_manager():
    return MagicMock(spec=RbacAuthorizationManager)


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="USR-200",
        username="factory_manager_b",
        company_id="TENANT_B",
        role=UserRoleEnum.FACTORY_MANAGER,
    )


@pytest.fixture
def target_system(
    mock_query_repo,
    mock_command_repo,
    mock_gen_quote_uc,
    mock_prod_order_uc,
    mock_rbac_manager,
):
    with (
        patch(
            "kpi_b2b.b2b_procurement.application.layout_mirroring.layout_mirroring_usecase.GlobalSystemLogger"
        ),
        patch("kpi_b2b.facades.procurement_command_facade.GlobalSystemLogger"),
    ):
        mirroring_uc = LayoutMirroringUseCase(command_repo=mock_command_repo)

        facade = ProcurementCommandFacade(
            generate_quote_uc=mock_gen_quote_uc,
            mirroring_uc=mirroring_uc,
            process_production_order_uc=mock_prod_order_uc,
            command_repo=mock_command_repo,
            query_repo=mock_query_repo,
            rbac_manager=mock_rbac_manager,
        )

        yield facade, mock_command_repo, mock_query_repo, mock_rbac_manager


def test_create_expert_session_happy_path(target_system, valid_ctx):
    facade, mock_cmd_repo, mock_qry_repo, mock_rbac = target_system
    baseline_id = "BASELINE-3D-001"

    mock_qry_repo.get_baseline_owner.return_value = "TENANT_B"
    mock_rbac.validate_company_isolation.return_value = True

    result_dto = facade.create_expert_session(baseline_id=baseline_id, ctx=valid_ctx)

    mock_rbac.validate_company_isolation.assert_called_once_with(
        user_ctx=valid_ctx,
        target_company_id="TENANT_B",
        target_resource=f"BASELINE:{baseline_id}",
    )

    mock_cmd_repo.save_expert_session.assert_called_once()
    saved_session = mock_cmd_repo.save_expert_session.call_args[0][0]

    assert saved_session.baseline_id == baseline_id
    assert saved_session.expert_id == "UNASSIGNED"
    assert saved_session.status == ExpertSessionStatusEnum.WAITING
    assert saved_session.session_token.startswith("TKN-")

    assert result_dto.session_id.startswith("SESS-")
    assert result_dto.session_token == saved_session.session_token
    assert result_dto.status == ExpertSessionStatusEnum.WAITING.value
    assert result_dto.expires_in_seconds == 14400


def test_create_expert_session_isolation_violation(target_system):
    facade, mock_cmd_repo, mock_qry_repo, mock_rbac = target_system

    invalid_ctx = UserContext(
        user_id="USR-HACKER",
        username="unauthorized_user",
        company_id="UNAUTHORIZED_TENANT",
        role=UserRoleEnum.CREATOR,
    )
    baseline_id = "BASELINE-SECRET-001"

    mock_qry_repo.get_baseline_owner.return_value = "ORIGINAL_OWNER_TENANT"
    mock_rbac.validate_company_isolation.side_effect = BaseSystemException(
        error_code=GlobalErrorCodeEnum.ERR_COMMON_FORBIDDEN,
        message="Multitenancy isolation policy violation.",
        status_code=403,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        facade.create_expert_session(baseline_id=baseline_id, ctx=invalid_ctx)

    assert exc_info.value.error_code == GlobalErrorCodeEnum.ERR_COMMON_FORBIDDEN
    assert exc_info.value.status_code == 403
    mock_cmd_repo.save_expert_session.assert_not_called()


def test_create_expert_session_db_failure(target_system, valid_ctx):
    facade, mock_cmd_repo, mock_qry_repo, mock_rbac = target_system
    baseline_id = "BASELINE-ERROR-001"

    mock_qry_repo.get_baseline_owner.return_value = "TENANT_B"
    mock_rbac.validate_company_isolation.return_value = True
    mock_cmd_repo.save_expert_session.side_effect = Exception(
        "OperationalError: Connection lost"
    )

    with pytest.raises(BaseSystemException) as exc_info:
        facade.create_expert_session(baseline_id=baseline_id, ctx=valid_ctx)

    assert exc_info.value.error_code == GlobalErrorCodeEnum.ERR_COMMON_INTERNAL_ERROR
    assert exc_info.value.status_code == 500
    assert "시스템 내부 장애가 발생했습니다" in exc_info.value.message
