from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.asset_library.domain.asset.kinematics_schema_key_enum import (
    KinematicsSchemaKey,
)
from digital_twin.ports.inbound.dtos.asset_dto import AssetDto
from digital_twin.twin_reconstruction.application.reconstruct_twin.raw_factory_data_dto import (
    RawFactoryDataDto,
)
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.enums.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException

from dependencies import DigitalTwinContainer, InfraContainer


@pytest.fixture
def mock_infra() -> InfraContainer:
    """실제 DB 없이 동작하는 Mock InfraContainer 생성"""
    infra = InfraContainer()
    mock_session_factory = MagicMock()
    mock_session = MagicMock()
    mock_session_factory.get_session.return_value.__enter__.return_value = mock_session
    mock_session_factory.get_session.return_value.__exit__.return_value = None
    infra.session_factory = mock_session_factory
    return infra


@pytest.fixture
def dt_container(mock_infra: InfraContainer) -> DigitalTwinContainer:
    """Mock 어댑터를 장착한 DigitalTwinContainer 생성"""
    return DigitalTwinContainer(infra=mock_infra)


@pytest.fixture
def test_user_context() -> UserContext:
    """실제 UserContext 필드 규격에 맞춘 테스트 컨텍스트 생성"""
    return UserContext(
        user_id="USR-TEST-001",
        username="tester",
        company_id="COMP-SFTWIN",
        role=UserRole.SYSTEM_ADMIN,
        accessible_factory_ids=["FACTORY-01"],
        is_edge_authenticated=False,
    )


# ==============================================================================
# 1. Asset Library Facade Tests (Register & Get Asset)
# ==============================================================================


def test_register_asset_success(
    dt_container: DigitalTwinContainer, test_user_context: UserContext
):
    """자산 등록(Command Facade) 성공 파이프라인 검증"""
    cmd_facade = dt_container.get_command_facade()

    # KinematicsSchemaKey 필수 키: degrees_of_freedom, dh_parameters
    asset_dto = AssetDto(
        asset_id="",
        asset_name="Doosan_M1013_Robot",
        asset_type="ROBOT",
        cad_file_path="/app/assets/cad/doosan_m1013.stl",
        kinematics_metadata={
            KinematicsSchemaKey.DEGREES_OF_FREEDOM.value: 6,
            KinematicsSchemaKey.DH_PARAMETERS.value: {
                "a": [0, -400, 0],
                "alpha": [1.57, 0, 1.57],
                "d": [0, 0, 0],
                "theta": [0, 0, 0],
            },
        },
    )

    mock_saved_entity = SimpleNamespace(asset_id="AST-M1013-001")
    dt_container._asset_adapter.save = MagicMock(return_value=mock_saved_entity)

    saved_asset_id = cmd_facade.register_asset(
        asset_dto=asset_dto, ctx=test_user_context
    )
    assert saved_asset_id == "AST-M1013-001"
    dt_container._asset_adapter.save.assert_called_once()


def test_get_asset_success(
    dt_container: DigitalTwinContainer, test_user_context: UserContext
):
    """자산 조회(Query Facade) 성공 파이프라인 검증"""
    query_facade = dt_container.get_query_facade()

    # Query Repo Mock 세팅: get_asset_usecase의 company_id 일치 조건 반영
    mock_entity = SimpleNamespace(
        asset_id="AST-M1013-001",
        asset_name="Doosan_M1013_Robot",
        asset_type=AssetType.ROBOT,
        cad_file_path="/app/assets/cad/doosan_m1013.stl",
        kinematics_metadata={
            "degrees_of_freedom": 6,
            "max_payload_kg": 13.0,
        },
        created_at="2026-08-23T00:00:00Z",
        is_deleted=False,
        company_id=test_user_context.company_id,
    )
    dt_container._asset_adapter.find_by_id = MagicMock(return_value=mock_entity)

    result_dto = query_facade.get_asset(asset_id="AST-M1013-001", ctx=test_user_context)
    assert result_dto.asset_id == "AST-M1013-001"
    assert result_dto.asset_name == "Doosan_M1013_Robot"
    assert result_dto.asset_type == "ROBOT"


def test_get_asset_access_denied(
    dt_container: DigitalTwinContainer, test_user_context: UserContext
):
    """타사 자산 조회 시 예외 발생(403/NotFound) 검증"""
    query_facade = dt_container.get_query_facade()

    # 타사 소유 엔티티
    mock_entity = SimpleNamespace(
        asset_id="AST-OTHER-001",
        asset_name="Other Robot",
        asset_type=AssetType.ROBOT,
        cad_file_path=None,
        kinematics_metadata=None,
        created_at="2026-08-23T00:00:00Z",
        is_deleted=False,
        company_id="COMP-OTHER",
    )
    dt_container._asset_adapter.find_by_id = MagicMock(return_value=mock_entity)

    with pytest.raises(BaseSystemException) as exc_info:
        query_facade.get_asset(asset_id="AST-OTHER-001", ctx=test_user_context)
    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND


# ==============================================================================
# 2. Twin Reconstruction Facade Tests (Reconstruct & Get Layout)
# ==============================================================================


def test_reconstruct_twin_success(
    dt_container: DigitalTwinContainer, test_user_context: UserContext, tmp_path: Path
):
    """센서 데이터 파싱 및 베이스라인 복각(Command Facade) 검증"""
    cmd_facade = dt_container.get_command_facade()

    # ReconstructTwinUseCase의 finally 파일 정리 로직 대응 임시 파일 생성
    temp_log_file = tmp_path / "temp_sensor_log.csv"
    temp_log_file.write_text("timestamp,vibration\n1700000000,0.01\n")

    raw_data_dto = RawFactoryDataDto(
        baseline_name="Baseline_2026_Q1",
        source_log_path=str(temp_log_file),
    )

    # Parser & Baseline Repo Mock 세팅
    dt_container._sensor_parser.parse = MagicMock(return_value={"series": [1.0, 2.0]})

    mock_saved_baseline = SimpleNamespace(
        baseline_id="BSL-001",
        baseline_name="Baseline_2026_Q1",
        sync_error_rate=0.5,
        sync_status=SimpleNamespace(value="COMPLETED"),
        updated_at="2026-08-23T00:00:00Z",
    )
    dt_container._baseline_adapter.save = MagicMock(return_value=mock_saved_baseline)

    # ReconstructTwinUseCase 실행
    metrics = cmd_facade.reconstruct_twin(raw_data=raw_data_dto, ctx=test_user_context)

    assert metrics.baseline_id == "BSL-001"
    assert metrics.is_verified is True
    # usecase의 _cleanup_temp_files 동작으로 임시 파일이 삭제되었는지 검증
    assert not temp_log_file.exists()


def test_get_layout_success(
    dt_container: DigitalTwinContainer, test_user_context: UserContext
):
    """베이스라인 3D 레이아웃 및 히트맵 조회(Query Facade) 검증"""
    query_facade = dt_container.get_query_facade()

    # Baseline Query Repo Mock 세팅
    mock_raw_data = {
        "baseline_id": "FACTORY-01",
        "baseline_name": "Factory_01_Main_Layout",
        "company_id": test_user_context.company_id,
        "sync_error_rate": 0.02,
        "sync_status": "COMPLETED",
        "asset_mappings": [
            {
                "asset_id": "AST-M1013-001",
                "asset_name": "Doosan_M1013",
                "asset_type": "ROBOT",
                "position_xyz_json": {"x": 1.0, "y": 2.0, "z": 0.0},
            }
        ],
    }
    dt_container._baseline_adapter.find_by_id = MagicMock(return_value=mock_raw_data)

    layout_dto = query_facade.get_layout(
        baseline_id="FACTORY-01", ctx=test_user_context
    )
    assert layout_dto.baseline_id == "FACTORY-01"
    assert len(layout_dto.asset_mappings) == 1
    assert layout_dto.asset_mappings[0].asset_id == "AST-M1013-001"
