"""
===============================================================================
[File Name] test_manage_asset_usecase.py
[Location ] /tests/asset_twin/asset_library/application/test_manage_asset_usecase.py
[Description] ManageAssetUseCase 및 FDS/TC 시나리오 기반 단위 테스트
===============================================================================
"""

import uuid
from unittest.mock import MagicMock

import pytest
from asset_twin.asset_library.application.manage_asset.manage_asset_usecase import (
    ManageAssetUseCase,
)
from asset_twin.asset_library.domain.asset import Asset
from asset_twin.asset_library.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.dtos.asset_dto import AssetDto
from shared.enums.asset_type_enum import AssetTypeEnum
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.security.user_context import UserContext


def test_tc_happy_path_register_asset():
    """
    [TC-정상] 신규 자산 정상 등록 및 저장소 호출 검증
    """
    # Given
    mock_repo = MagicMock(spec=IAssetCommandRepository)

    def mock_save(entity: Asset):
        return entity

    mock_repo.save.side_effect = mock_save

    usecase = ManageAssetUseCase(command_repository=mock_repo)

    dto = AssetDto(
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

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRoleEnum.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )

    # When
    generated_asset_id = usecase.register_asset(dto, ctx)

    # Then
    # 1. 반환된 문자열이 유효한 UUID 형식인지 검증
    assert uuid.UUID(generated_asset_id) is not None
    # 2. Mock 저장소 save가 1회 호출되었는지 확인
    assert mock_repo.save.call_count == 1
    # 3. 전달된 Asset 객체의 company_id가 TEST-COMPANY-01로 매핑되었는지 단언
    saved_arg: Asset = mock_repo.save.call_args[0][0]
    assert saved_arg.company_id == "TEST-COMPANY-01"
    assert saved_arg.asset_name == "Doosan_M1013_Robot"


def test_tc_edge_case_tenant_isolation_forbidden():
    """
    [TC-예외] 타사 격리 자산 조회 시도 시 차단 및 Fallback 검증
    """
    # Given
    mock_repo = MagicMock(spec=IAssetCommandRepository)
    private_asset = Asset(
        asset_id="PRIVATE-ASSET-01",
        asset_name="Private_CNC",
        asset_type=AssetTypeEnum.CNC,
        company_id="OTHER-COMPANY-99",  # 타사 보유 자산
        kinematics_metadata={"degrees_of_freedom": 3, "dh_parameters": {}},
    )
    mock_repo.find_by_id.return_value = private_asset

    usecase = ManageAssetUseCase(command_repository=mock_repo)

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",  # 다른 요청 회사
        role=UserRoleEnum.FIELD_ENGINEER,
        accessible_factory_ids=[],
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.get_asset("PRIVATE-ASSET-01", ctx)

    # 보안상 존재 유무를 은닉하기 위해 404 ERR_TWIN_NOT_FOUND로 처리됨을 검증
    assert exc_info.value.error_code == GlobalErrorCodes.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404


def test_tc_error_handling_invalid_domain_schema():
    """
    [TC-에러] 도메인 스키마 규격 위반 시 조기 차단(Guard Clause) 검증
    """
    # Given
    mock_repo = MagicMock(spec=IAssetCommandRepository)
    usecase = ManageAssetUseCase(command_repository=mock_repo)

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
        role=UserRoleEnum.FIELD_ENGINEER,
        accessible_factory_ids=[],
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.register_asset(invalid_dto, ctx)

    assert exc_info.value.error_code == GlobalErrorCodes.ERR_TWIN_INVALID_SCHEMA
    assert exc_info.value.status_code == 400
    # Mock 저장소의 save() 메서드가 단 한 번도 호출되지 않았음을 단언
    mock_repo.save.assert_not_called()
