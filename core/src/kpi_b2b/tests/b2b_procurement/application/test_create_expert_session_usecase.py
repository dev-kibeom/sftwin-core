from unittest.mock import MagicMock

import pytest
from kpi_b2b.b2b_procurement.application.create_expert_session.create_expert_session_usecase import (
    CreateExpertSessionUseCase,
)
from kpi_b2b.contracts.dtos.session_data_dto import SessionDataDto
from kpi_b2b.contracts.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.contracts.ports.outbound.i_procurement_query_repository import (
    IProcurementQueryRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole


@pytest.fixture
def mock_command_repo() -> MagicMock:
    return MagicMock(spec=IProcurementCommandRepository)


@pytest.fixture
def mock_query_repo() -> MagicMock:
    return MagicMock(spec=IProcurementQueryRepository)


@pytest.fixture
def usecase(
    mock_command_repo: MagicMock, mock_query_repo: MagicMock
) -> CreateExpertSessionUseCase:
    return CreateExpertSessionUseCase(
        command_repo=mock_command_repo,
        query_repo=mock_query_repo,
    )


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


def test_tc_happy_path_create_expert_session(
    usecase: CreateExpertSessionUseCase,
    mock_command_repo: MagicMock,
    mock_query_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 테넌트 베이스라인 확인 후 세션 생성 및 영속화 검증"""
    mock_query_repo.exists_by_id_and_company.return_value = True

    result = usecase.execute(baseline_id="BASE-001", ctx=standard_context)

    mock_query_repo.exists_by_id_and_company.assert_called_once_with(
        baseline_id="BASE-001",
        company_id="TEST-COMPANY-01",
    )
    mock_command_repo.save_expert_session.assert_called_once()
    assert isinstance(result, SessionDataDto)
    assert result.session_id.startswith("SESS-")
    assert result.session_token.startswith("TKN-")
    assert result.status == "WAITING"
    assert result.expires_in_seconds == 14400


def test_tc_edge_case_baseline_not_found_or_unauthorized(
    usecase: CreateExpertSessionUseCase,
    mock_command_repo: MagicMock,
    mock_query_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-예외] 베이스라인이 없거나 타 테넌트일 때 404 NOT_FOUND 발생 및 세션 생성 차단 검증"""
    mock_query_repo.exists_by_id_and_company.return_value = False

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(baseline_id="INVALID-BASE", ctx=standard_context)

    mock_query_repo.exists_by_id_and_company.assert_called_once_with(
        baseline_id="INVALID-BASE",
        company_id="TEST-COMPANY-01",
    )
    mock_command_repo.save_expert_session.assert_not_called()
    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404
