"""
===============================================================================
[File Name] test_get_layout_usecase.py
[Location ] /tests/asset_twin/twin_reconstruction/application/test_get_layout_usecase.py
[Description] GetLayoutUseCase FDS 시나리오 기반 단위 테스트 (Happy Path, Isolation Check, Not Found)
===============================================================================
"""

from unittest.mock import MagicMock

import pytest

from src.asset_twin.twin_reconstruction.application.get_layout_usecase import (
    GetLayoutUseCase,
    ITwinQueryRepository,
)
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes
from src.shared.security.user_context import UserContext


def test_tc_happy_path_get_layout_data():
    """
    [TC-정상] 3D 렌더링용 레이아웃 데이터 조회 성공
    """
    # Given
    mock_repo = MagicMock(spec=ITwinQueryRepository)
    mock_repo.find_baseline_with_mappings.return_value = {
        "baseline_id": "BASE-TWIN-001",
        "baseline_name": "Smart_Factory_Line_1",
        "company_id": "TEST-COMPANY-01",
        "sync_error_rate": 1.25,
        "sync_status": "COMPLETED",
        "asset_mappings": [
            {
                "asset_id": "AAS-ROBOT-001",
                "asset_name": "Doosan_M1013",
                "asset_type": "ROBOT",
                "cad_file_path": "/models/doosan.gltf",
                "position_xyz_json": {"x": 10.0, "y": 0.0, "z": 5.0},
                "rotation_q_json": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
            }
        ],
    }

    usecase = GetLayoutUseCase(query_repository=mock_repo)

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRoleEnum.CREATOR,
        accessible_factory_ids=["BASE-TWIN-001"],
    )

    # When
    result = usecase.execute("BASE-TWIN-001", ctx)

    # Then
    assert result.baseline_id == "BASE-TWIN-001"
    assert result.company_id == "TEST-COMPANY-01"
    assert len(result.asset_mappings) == 1
    assert result.asset_mappings[0].asset_id == "AAS-ROBOT-001"
    assert result.asset_mappings[0].position_xyz_json == {"x": 10.0, "y": 0.0, "z": 5.0}
    assert mock_repo.find_baseline_with_mappings.call_count == 1


def test_tc_edge_case_unauthorized_isolation_violation():
    """
    [TC-예외] 인가되지 않은 타사 가상 공장 접근 시도 시 404로 은닉 차단
    """
    # Given
    mock_repo = MagicMock(spec=ITwinQueryRepository)
    mock_repo.find_baseline_with_mappings.return_value = {
        "baseline_id": "PRIVATE-TWIN-999",
        "baseline_name": "Other_Company_Factory",
        "company_id": "OTHER-COMPANY-99",  # 타사 보유
        "sync_error_rate": 0.5,
        "sync_status": "COMPLETED",
        "asset_mappings": [],
    }

    usecase = GetLayoutUseCase(query_repository=mock_repo)

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",  # 권한 없는 다른 회사
        role=UserRoleEnum.CREATOR,
        accessible_factory_ids=["OTHER-FACTORY-01"],  # 해당 베이스라인 미포함
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute("PRIVATE-TWIN-999", ctx)

    # 보안 정책상 404 ERR_TWIN_NOT_FOUND로 은닉 처리되었는지 확인
    assert exc_info.value.error_code == GlobalErrorCodes.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404


def test_tc_error_handling_baseline_not_found():
    """
    [TC-에러] 존재하지 않는 베이스라인 데이터 요청 시 차단
    """
    # Given
    mock_repo = MagicMock(spec=ITwinQueryRepository)
    mock_repo.find_baseline_with_mappings.return_value = None  # DB 결과 없음

    usecase = GetLayoutUseCase(query_repository=mock_repo)

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRoleEnum.CREATOR,
        accessible_factory_ids=[],
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute("INVALID-TWIN-000", ctx)

    assert exc_info.value.error_code == GlobalErrorCodes.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404
