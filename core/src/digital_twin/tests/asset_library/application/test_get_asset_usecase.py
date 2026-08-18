from unittest.mock import MagicMock

import pytest
from digital_twin.asset_library.application.get_asset.get_asset_usecase import (
    GetAssetUseCase,
)
from digital_twin.asset_library.domain.asset import Asset
from digital_twin.asset_library.domain.enums.asset_type_enum import AssetTypeEnum
from digital_twin.ports.inbound.dtos.asset_dto import AssetDto
from digital_twin.ports.outbound.i_asset_query_repository import IAssetQueryRepository
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.enums.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException


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
    """
    [TC-정상] 동일 테넌트의 유효 자산 조회 성공 및 AssetDto 매핑 검증
    """
    # Given
    valid_asset = Asset(
        asset_id="VALID-CNC-01",
        asset_name="Standard_CNC",
        asset_type=AssetTypeEnum.CNC,
        company_id="TEST-COMPANY-01",
        cad_file_path="/cad/models/cnc_01.step",
        kinematics_metadata={"degrees_of_freedom": 3, "dh_parameters": {}},
        is_deleted=False,
        created_at="2026-07-31T00:00:00Z",
    )
    mock_query_repo.find_by_id.return_value = valid_asset

    # When
    result = usecase.execute("VALID-CNC-01", standard_context)

    # Then
    mock_query_repo.find_by_id.assert_called_once_with("VALID-CNC-01")
    assert isinstance(result, AssetDto)
    assert result.asset_id == "VALID-CNC-01"
    assert result.asset_name == "Standard_CNC"
    assert result.asset_type == AssetTypeEnum.CNC.value
    assert result.cad_file_path == "/cad/models/cnc_01.step"
    assert result.kinematics_metadata == {"degrees_of_freedom": 3, "dh_parameters": {}}
    assert result.created_at == "2026-07-31T00:00:00Z"


def test_tc_edge_case_asset_not_found(
    usecase: GetAssetUseCase,
    mock_query_repo: MagicMock,
    standard_context: UserContext,
):
    """
    [TC-예외] DB에 해당 asset_id가 존재하지 않을 때 404 NOT_FOUND 반환 검증
    """
    # Given
    mock_query_repo.find_by_id.return_value = None

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute("NON-EXISTENT-ID", standard_context)

    mock_query_repo.find_by_id.assert_called_once_with("NON-EXISTENT-ID")
    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404


def test_tc_edge_case_soft_deleted_asset(
    usecase: GetAssetUseCase,
    mock_query_repo: MagicMock,
    standard_context: UserContext,
):
    """
    [TC-예외] 논리 삭제(is_deleted=True)된 자산 조회 시 은닉(404) 처리 검증
    """
    # Given
    deleted_asset = Asset(
        asset_id="DELETED-CNC-01",
        asset_name="Deleted_CNC",
        asset_type=AssetTypeEnum.CNC,
        company_id="TEST-COMPANY-01",
        kinematics_metadata={},
        is_deleted=True,
    )
    mock_query_repo.find_by_id.return_value = deleted_asset

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute("DELETED-CNC-01", standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404


def test_tc_edge_case_tenant_isolation_forbidden(
    usecase: GetAssetUseCase,
    mock_query_repo: MagicMock,
    standard_context: UserContext,
):
    """
    [TC-예외] 타사 격리 자산(company_id 불일치) 조회 시 차단 및 404 은닉 검증
    """
    # Given
    private_asset = Asset(
        asset_id="PRIVATE-ASSET-01",
        asset_name="Private_CNC",
        asset_type=AssetTypeEnum.CNC,
        company_id="OTHER-COMPANY-99",
        kinematics_metadata={"degrees_of_freedom": 3, "dh_parameters": {}},
        is_deleted=False,
    )
    mock_query_repo.find_by_id.return_value = private_asset

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute("PRIVATE-ASSET-01", standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404
