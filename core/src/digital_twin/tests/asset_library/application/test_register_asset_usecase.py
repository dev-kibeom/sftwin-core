import uuid
from unittest.mock import MagicMock

import pytest
from digital_twin.asset_library.application.register_asset.register_asset_usecase import (
    RegisterAssetUseCase,
)
from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.ports.inbound.dtos.asset_dto import AssetDto
from digital_twin.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException


def test_tc_happy_path_register_asset():
    """
    [TC-정상] 신규 자산 정상 등록 및 저장소 호출 검증
    """
    # Given
    mock_repo = MagicMock(spec=IAssetCommandRepository)

    def mock_save(entity: Asset):
        return entity

    mock_repo.save.side_effect = mock_save

    usecase = RegisterAssetUseCase(command_repo=mock_repo)

    valid_asset_dto = AssetDto(
        asset_id="",
        asset_name="Doosan_M1013_Robot",
        asset_type="ROBOT",
        cad_file_path="/models/doosan.gltf",
        kinematics_metadata={
            "degrees_of_freedom": 6,
            "dh_parameters": {"a": [0, -425, -392]},
        },
        created_at="2026-07-31T00:00:00Z",
    )

    valid_user_ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )

    # When
    generated_asset_id = usecase.execute(valid_asset_dto, valid_user_ctx)

    # Then
    # 1. 반환된 문자열이 유효한 UUID 형식인지 검증
    assert uuid.UUID(generated_asset_id) is not None
    # 2. Mock 저장소 save가 1회 호출되었는지 확인
    assert mock_repo.save.call_count == 1
    # 3. 전달된 Asset 객체의 company_id가 TEST-COMPANY-01로 매핑되었는지 단언
    saved_arg: Asset = mock_repo.save.call_args[0][0]
    assert saved_arg.company_id == "TEST-COMPANY-01"
    assert saved_arg.asset_name == "Doosan_M1013_Robot"


def test_tc_error_handling_invalid_domain_schema():
    """
    [TC-에러] 도메인 스키마 규격 위반 시 조기 차단(Guard Clause) 검증
    """
    # Given
    mock_repo = MagicMock(spec=IAssetCommandRepository)

    usecase = RegisterAssetUseCase(command_repo=mock_repo)

    # kinematics_metadata 필수 규격 누락 DTO
    invalid_dto = AssetDto(
        asset_id="",
        asset_name="Invalid_Robot",
        asset_type="ROBOT",
        cad_file_path=None,
        kinematics_metadata={},  # degrees_of_freedom 누락
        created_at="2026-07-31T00:00:00Z",
    )

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=[],
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(invalid_dto, ctx)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA
    assert exc_info.value.status_code == 400
    # Mock 저장소의 save() 메서드가 단 한 번도 호출되지 않았음을 단언
    mock_repo.save.assert_not_called()
