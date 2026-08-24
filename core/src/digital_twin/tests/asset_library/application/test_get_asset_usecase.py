from unittest.mock import MagicMock

import pytest
from digital_twin.asset_library.application.get_asset.get_asset_usecase import (
    GetAssetUseCase,
)
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.contracts.dtos.asset_dto import AssetDto
from digital_twin.contracts.ports.outbound.i_asset_query_repository import (
    IAssetQueryRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole


@pytest.fixture
def mock_query_repo() -> MagicMock:
    return MagicMock(spec=IAssetQueryRepository)


@pytest.fixture
def usecase(mock_query_repo: MagicMock) -> GetAssetUseCase:
    return GetAssetUseCase(query_repo=mock_query_repo)


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


def test_tc_happy_path_get_asset(
    usecase: GetAssetUseCase,
    mock_query_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 테넌트 자산 DTO 정상 반환 및 호출 파라미터 검증"""
    expected_dto = AssetDto(
        asset_id="VALID-CNC-01",
        asset_name="Standard_CNC",
        asset_type=AssetType.CNC,
        cad_file_path="/cad/models/cnc_01.step",
        kinematics_metadata={"degrees_of_freedom": 3, "dh_parameters": {}},
        created_at="2026-07-31T00:00:00Z",
    )
    mock_query_repo.find_by_id.return_value = expected_dto

    result = usecase.execute("VALID-CNC-01", standard_context)

    mock_query_repo.find_by_id.assert_called_once_with(
        asset_id="VALID-CNC-01",
        company_id="TEST-COMPANY-01",
    )
    assert result == expected_dto


def test_tc_edge_case_asset_not_found(
    usecase: GetAssetUseCase,
    mock_query_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-예외] 자산이 없거나 접근 불가능할 때 404 NOT_FOUND 발생 검증"""
    mock_query_repo.find_by_id.return_value = None

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute("NON-EXISTENT-ID", standard_context)

    mock_query_repo.find_by_id.assert_called_once_with(
        asset_id="NON-EXISTENT-ID",
        company_id="TEST-COMPANY-01",
    )
    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404
