import json
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


class DummyAssetType(str, Enum):
    ROBOT_ARM = "ROBOT_ARM"


@pytest.fixture
def mock_session_factory():
    factory = MagicMock()
    session = MagicMock()
    factory.get_session.return_value = session
    return factory


@pytest.fixture
def mock_system_logger():
    return MagicMock()


@pytest.fixture
def mock_audit_logger():
    return MagicMock()


@pytest.fixture
def mock_mapper():
    mapper = MagicMock()
    return mapper


@pytest.fixture
def adapter(mock_session_factory, mock_mapper, mock_system_logger, mock_audit_logger):
    return AssetPersistenceAdapter(
        session_factory=mock_session_factory,
        mapper=mock_mapper,
        aas_storage_dir="data/assets/aas",
        system_logger=mock_system_logger,
        audit_logger=mock_audit_logger,
    )


@pytest.fixture
def sample_orm_model():
    return AssetOrmModel(
        asset_id="AST-001",
        company_id="COMP-A",
        asset_name="RobotArm_X1",
        asset_type="ROBOT_ARM",
        kinematics_metadata={"dof": 6, "joints": [{"name": "j1"}]},
        cad_file_path="/cad/arm.step",
        aas_file_path="data/assets/aas/COMP-A/AST-001.json",
        is_deleted=False,
    )


def test_tc_aas_007_happy_path_full_hit(
    adapter, mock_session_factory, mock_mapper, sample_orm_model
):
    session = mock_session_factory.get_session.return_value
    session.query.return_value.filter.return_value.first.return_value = sample_orm_model

    mock_asset = MagicMock(spec=Asset)
    mock_mapper.to_domain_entity.return_value = mock_asset

    aas_file_data = {
        "asset_id": "AST-001",
        "submodels": {"kinematics": {"dof": 6}},
    }

    with (
        patch.object(Path, "exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(aas_file_data))),
    ):
        result = adapter.find_by_id("AST-001")

    assert result == mock_asset
    assert session.close.call_count == 1
    mock_mapper.to_domain_entity.assert_called_once_with(
        sample_orm_model, aas_file_data
    )


def test_tc_aas_008_fallback_path_file_missing(
    adapter, mock_session_factory, mock_mapper, mock_system_logger, sample_orm_model
):
    session = mock_session_factory.get_session.return_value
    session.query.return_value.filter.return_value.first.return_value = sample_orm_model

    mock_asset = MagicMock(spec=Asset)
    mock_mapper.to_domain_entity.return_value = mock_asset

    with patch.object(Path, "exists", return_value=False):
        result = adapter.find_by_id("AST-001")

    assert result == mock_asset
    assert mock_system_logger.warn.call_count == 1
    expected_fallback_payload = {
        "submodels": {"kinematics": sample_orm_model.kinematics_metadata}
    }
    mock_mapper.to_domain_entity.assert_called_once_with(
        sample_orm_model, expected_fallback_payload
    )


def test_tc_aas_009_not_found(adapter, mock_session_factory, mock_mapper):
    session = mock_session_factory.get_session.return_value
    session.query.return_value.filter.return_value.first.return_value = None

    result = adapter.find_by_id("NON-EXISTENT")

    assert result is None
    assert session.close.call_count == 1
    mock_mapper.to_domain_entity.assert_not_called()


def test_tc_aas_010_db_operational_failure(adapter, mock_session_factory):
    session = mock_session_factory.get_session.return_value
    session.query.return_value.filter.side_effect = OperationalError(
        "DB connection lost", params=None, orig=Exception()
    )

    with pytest.raises(BaseSystemException) as exc_info:
        adapter.find_by_id("AST-001")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_DB_CONNECTION_FAILED
    assert session.rollback.call_count == 1
    assert session.close.call_count == 1
