from enum import Enum
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from digital_twin.asset_library.domain.asset.asset import Asset
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from sqlalchemy.exc import OperationalError

from plugins.aas_persistence.adapters.asset_persistence_adapter import (
    AssetPersistenceAdapter,
)
from plugins.aas_persistence.models.asset_orm_model import AssetOrmModel
from plugins.aas_persistence.validators.aas_json_schema_validator import (
    AasJsonSchemaValidator,
    SchemaValidationError,
)


class DummyAssetType(str, Enum):
    """테스트용 더미 AssetType Enum."""

    ROBOT_ARM = "ROBOT_ARM"


@pytest.fixture
def mock_session_factory():
    """DatabaseSessionFactory 목 객체 생성 픽스처."""
    factory = MagicMock()
    session = MagicMock()
    factory.get_session.return_value = session
    return factory


@pytest.fixture
def mock_validator():
    """AasJsonSchemaValidator 목 객체 생성 픽스처."""
    validator = MagicMock(spec=AasJsonSchemaValidator)
    validator.validate_kinematics_json.return_value = True
    validator.validate_aas_submodels.return_value = True
    return validator


@pytest.fixture
def mock_mapper():
    """AssetEntityMapper 목 객체 생성 픽스처."""
    mapper = MagicMock()
    mapper.to_orm_model.return_value = AssetOrmModel(
        asset_id="AST-001",
        company_id="COMP-A",
        asset_name="RobotArm_X1",
        asset_type="ROBOT_ARM",
        kinematics_metadata={"dof": 6, "joints": []},
        cad_file_path="/cad/arm.step",
        aas_file_path="data/assets/aas/COMP-A/AST-001.json",
        is_deleted=False,
    )
    return mapper


@pytest.fixture
def mock_system_logger():
    """GlobalSystemLogger 목 객체 생성 픽스처."""
    return MagicMock()


@pytest.fixture
def mock_audit_logger():
    """GlobalAuditLogger 목 객체 생성 픽스처."""
    return MagicMock()


@pytest.fixture
def valid_asset():
    """테스트용 유효한 Asset 엔티티 목 객체."""
    asset = MagicMock(spec=Asset)
    asset.asset_id = "AST-001"
    asset.company_id = "COMP-A"
    asset.asset_name = "RobotArm_X1"
    asset.asset_type = DummyAssetType.ROBOT_ARM
    asset.kinematics_metadata = {
        "dof": 6,
        "joints": [
            {
                "name": "joint_1",
                "type": "revolute",
                "min_limit": -3.14,
                "max_limit": 3.14,
            }
        ],
    }
    asset.cad_file_path = "/cad/arm.step"
    asset.submodels = {"identification": {"id": "AST-001"}}
    return asset


@pytest.fixture
def adapter(
    mock_session_factory,
    mock_validator,
    mock_mapper,
    mock_system_logger,
    mock_audit_logger,
):
    """SUT (AssetPersistenceAdapter) 인스턴스 생성 픽스처."""
    return AssetPersistenceAdapter(
        session_factory=mock_session_factory,
        validator=mock_validator,
        mapper=mock_mapper,
        aas_storage_dir="data/assets/aas",
        system_logger=mock_system_logger,
        audit_logger=mock_audit_logger,
    )


def test_tc_aas_001_happy_path_save(adapter, valid_asset, mock_session_factory):
    """TC-AAS-001: Asset 신규/수정 정상 영속화 플로우 검증."""
    session = mock_session_factory.get_session.return_value

    with (
        patch("builtins.open", mock_open()) as _,
        patch("os.replace") as mock_replace,
        patch.object(Path, "mkdir") as _,
    ):
        result = adapter.save(valid_asset)

    # 1. 반환된 Asset 인스턴스 검증
    assert result == valid_asset

    # 2. 임시 파일 -> 원본 파일 원자적 교체 호출 검증
    assert mock_replace.call_count == 1

    # 3. DB 세션 merge 및 commit 호출 검증
    assert session.merge.call_count == 1
    assert session.commit.call_count == 1
    assert session.close.call_count == 1


def test_tc_aas_002_happy_path_delete(adapter, mock_session_factory, mock_audit_logger):
    """TC-AAS-002: Asset 소프트 삭제 및 보안 감사 이벤트 발행 검증."""
    session = mock_session_factory.get_session.return_value
    mock_record = MagicMock(spec=AssetOrmModel)
    mock_record.is_deleted = False

    # DB 쿼리 체이닝 모킹
    session.query.return_value.filter.return_value.first.return_value = mock_record

    result = adapter.delete("AST-001")

    # 1. 반환값 및 상태 플래그 검증
    assert result is True
    assert mock_record.is_deleted is True

    # 2. DB 커밋 및 세션 정리 검증
    assert session.commit.call_count == 1
    assert session.close.call_count == 1

    # 3. 보안 감사 로그 호출 검증
    assert mock_audit_logger.log_security_event.call_count == 1
    audit_call_arg = mock_audit_logger.log_security_event.call_args[0][0]
    assert audit_call_arg.action == "DELETE_ASSET"
    assert audit_call_arg.target == "ASSET:AST-001"


def test_tc_aas_003_validation_failure_invalid_kinematics(
    adapter, valid_asset, mock_validator, mock_session_factory
):
    """TC-AAS-003: Kinematics JSON 규격 위반 시 ERR_TWIN_INVALID_SCHEMA 발생 검증."""
    mock_validator.validate_kinematics_json.side_effect = SchemaValidationError(
        "Missing required field 'joints'", details={"missing_field": "joints"}
    )

    with (
        patch("builtins.open", mock_open()) as mock_file,
        pytest.raises(BaseSystemException) as exc_info,
    ):
        adapter.save(valid_asset)

    # 1. 예외 코드 및 상태 검증
    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA

    # 2. 파일 I/O 및 DB 트랜잭션 진입 차단 검증
    mock_file.assert_not_called()
    mock_session_factory.get_session.assert_not_called()


def test_tc_aas_004_file_io_failure(adapter, valid_asset, mock_session_factory):
    """TC-AAS-004: 파일 시스템 기록 실패 시 ERR_COMMON_INTERNAL_ERROR 및 DB 호출 차단 검증."""
    with (
        patch(
            "builtins.open", side_effect=PermissionError("Disk write permission denied")
        ),
        patch.object(Path, "mkdir"),
        pytest.raises(BaseSystemException) as exc_info,
    ):
        adapter.save(valid_asset)

    # 1. 내부 시스템 예외 변환 검증
    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR

    # 2. DB 트랜잭션 미호출 검증
    mock_session_factory.get_session.assert_not_called()


def test_tc_aas_005_db_error_and_compensating_file_rollback(
    adapter, valid_asset, mock_session_factory
):
    """TC-AAS-005: DB 저장 실패 시 보상 트랜잭션(물리 파일 삭제) 및 ERR_DB_CONNECTION_FAILED 발생 검증."""
    session = mock_session_factory.get_session.return_value
    session.commit.side_effect = OperationalError(
        "MySQL server has gone away", params=None, orig=Exception()
    )

    with (
        patch("builtins.open", mock_open()) as _,
        patch("os.replace") as _,
        patch.object(Path, "mkdir") as _,
        patch.object(Path, "exists", return_value=True),
        patch("os.remove") as mock_remove,
        pytest.raises(BaseSystemException) as exc_info,
    ):
        adapter.save(valid_asset)

    # 1. DB 롤백 호출 검증
    assert session.rollback.call_count == 1
    assert session.close.call_count == 1

    # 2. 보상 트랜잭션(물리 파일 os.remove) 호출 검증
    assert mock_remove.call_count == 1

    # 3. DB 예외 변환 검증
    assert exc_info.value.error_code == GlobalErrorCode.ERR_DB_CONNECTION_FAILED


def test_tc_aas_006_delete_target_not_found(
    adapter, mock_session_factory, mock_audit_logger
):
    """TC-AAS-006: 삭제 대상 레코드 미존재 시 False 반환 및 감사 로그 생략 검증."""
    session = mock_session_factory.get_session.return_value
    session.query.return_value.filter.return_value.first.return_value = None

    result = adapter.delete("NON-EXISTENT-ID")

    # 1. False 반환 및 커밋 미실행 검증
    assert result is False
    assert session.commit.call_count == 0
    assert session.close.call_count == 1

    # 2. 감사 로그 미발행 검증
    assert mock_audit_logger.log_security_event.call_count == 0
