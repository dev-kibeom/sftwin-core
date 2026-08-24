from unittest.mock import MagicMock

import pytest
from digital_twin.asset_library.application.register_asset.register_asset_usecase import (
    RegisterAssetUseCase,
)
from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.dtos.asset_dto import AssetDto
from digital_twin.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole


@pytest.fixture
def mock_command_repo() -> MagicMock:
    return MagicMock(spec=IAssetCommandRepository)


@pytest.fixture
def usecase(mock_command_repo: MagicMock) -> RegisterAssetUseCase:
    return RegisterAssetUseCase(command_repo=mock_command_repo)


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


@pytest.fixture
def valid_asset_dto() -> AssetDto:
    return AssetDto(
        asset_id="",
        asset_name="Doosan_M1013_Robot",
        asset_type=AssetType.ROBOT,
        cad_file_path="/models/doosan.gltf",
        kinematics_metadata={
            "degrees_of_freedom": 6,
            "dh_parameters": {"a": [0, -425, -392]},
        },
        created_at="2026-07-31T00:00:00Z",
    )


def test_tc_happy_path_register_asset(
    usecase: RegisterAssetUseCase,
    mock_command_repo: MagicMock,
    standard_context: UserContext,
    valid_asset_dto: AssetDto,
):
    """
    [TC-정상] 엔티티 변환, 컨텍스트 정보(company_id, user_id) 주입 및 영속화 호출 검증
    """
    # Given: save 호출 시 전달된 Asset 엔티티에 생성된 asset_id를 포함해 반환하도록 모킹
    mock_saved_asset = MagicMock(spec=Asset)
    mock_saved_asset.asset_id = "GENERATED-UUID-01"
    mock_saved_asset.asset_name = valid_asset_dto.asset_name
    mock_command_repo.save.return_value = mock_saved_asset

    # When
    registered_id = usecase.execute(valid_asset_dto, standard_context)

    # Then
    assert registered_id == "GENERATED-UUID-01"
    mock_command_repo.save.assert_called_once()

    # Domain Entity 변환 및 컨텍스트 바인딩 값 검증
    saved_entity: Asset = mock_command_repo.save.call_args[0][0]
    assert saved_entity.asset_name == valid_asset_dto.asset_name
    assert saved_entity.asset_type == valid_asset_dto.asset_type
    assert saved_entity.company_id == standard_context.company_id
    assert saved_entity.created_by == standard_context.user_id
    assert saved_entity.updated_by == standard_context.user_id


def test_tc_error_handling_invalid_domain_schema(
    usecase: RegisterAssetUseCase,
    mock_command_repo: MagicMock,
    standard_context: UserContext,
):
    """
    [TC-에러] Asset 도메인 생성자 검증 실패 시 ERR_TWIN_INVALID_SCHEMA 변환 및 영속화 차단 검증
    """
    # Given: 도메인 유효성 검증 실패를 유도하는 잘못된 DTO
    invalid_dto = AssetDto(
        asset_id="",
        asset_name="Invalid_Robot",
        asset_type=AssetType.ROBOT,
        cad_file_path=None,
        kinematics_metadata={},
        created_at="2026-07-31T00:00:00Z",
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(invalid_dto, standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA
    mock_command_repo.save.assert_not_called()
