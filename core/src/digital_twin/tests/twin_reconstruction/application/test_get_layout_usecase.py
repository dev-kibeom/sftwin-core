from unittest.mock import MagicMock

import pytest
from digital_twin.ports.outbound.i_baseline_query_repository import (
    IBaselineQueryRepository,
)
from digital_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
)
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException


@pytest.fixture
def mock_query_repo():
    return MagicMock(spec=IBaselineQueryRepository)


@pytest.fixture
def usecase(mock_query_repo):
    return GetLayoutUseCase(query_repo=mock_query_repo)


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRoleEnum.CREATOR,
        accessible_factory_ids=["BASE-TWIN-001"],
    )


@pytest.fixture
def unauthorized_ctx():
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",  # 타사 공장 접근 시도용
        role=UserRoleEnum.CREATOR,
        accessible_factory_ids=["OTHER-FACTORY-01"],
    )


def test_tc_happy_path_get_layout_data(usecase, mock_query_repo, valid_ctx):
    """
    [TC-정상] 3D 렌더링용 레이아웃 데이터 조회 성공
    """
    # Given
    mock_query_repo.find_by_id.return_value = {
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

    # When
    result = usecase.execute("BASE-TWIN-001", valid_ctx)

    # Then
    assert result.baseline_id == "BASE-TWIN-001"
    assert result.company_id == "TEST-COMPANY-01"
    assert len(result.asset_mappings) == 1
    assert result.asset_mappings[0].asset_id == "AAS-ROBOT-001"
    assert result.asset_mappings[0].position_xyz_json == {"x": 10.0, "y": 0.0, "z": 5.0}
    assert mock_query_repo.find_by_id.call_count == 1


def test_tc_edge_case_unauthorized_isolation_violation(
    usecase, mock_query_repo, unauthorized_ctx
):
    """
    [TC-예외] 인가되지 않은 타사 가상 공장 접근 시도 시 404로 은닉 차단
    """
    # Given: 타사 보유 공장 데이터 Mocking
    mock_query_repo.find_by_id.return_value = {
        "baseline_id": "PRIVATE-TWIN-999",
        "baseline_name": "Other_Company_Factory",
        "company_id": "OTHER-COMPANY-99",
        "sync_error_rate": 0.5,
        "sync_status": "COMPLETED",
        "asset_mappings": [],
    }

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute("PRIVATE-TWIN-999", unauthorized_ctx)

    assert exc_info.value.error_code == GlobalErrorCodeEnum.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404


def test_tc_error_handling_baseline_not_found(usecase, mock_query_repo, valid_ctx):
    """
    [TC-에러] 존재하지 않는 베이스라인 데이터 요청 시 차단
    """
    # Given
    mock_query_repo.find_by_id.return_value = None

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute("INVALID-TWIN-000", valid_ctx)

    assert exc_info.value.error_code == GlobalErrorCodeEnum.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404
