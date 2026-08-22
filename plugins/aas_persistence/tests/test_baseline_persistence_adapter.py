from enum import Enum
from unittest.mock import MagicMock

import pytest
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from sqlalchemy.exc import OperationalError

from plugins.aas_persistence.adapters.baseline_persistence_adapter import (
    BaselinePersistenceAdapter,
)
from plugins.aas_persistence.models.baseline_orm_model import BaselineOrmModel


class DummyTwinSyncStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"


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
    mapper.to_orm_model.return_value = BaselineOrmModel(
        baseline_id="BASE-001",
        company_id="COMP-A",
        baseline_name="Baseline_Model_X1",
        sync_error_rate=0.0350,
        sync_status="COMPLETED",
        raw_sensor_summary={"mean": 12.5},
        is_deleted=False,
    )
    return mapper


@pytest.fixture
def valid_baseline():
    baseline = MagicMock(spec=TwinBaseline)
    baseline.baseline_id = "BASE-001"
    baseline.company_id = "COMP-A"
    baseline.baseline_name = "Baseline_Model_X1"
    baseline.source_log_path = "/logs/source.csv"
    baseline.sync_error_rate = 0.0350
    baseline.sync_status = DummyTwinSyncStatus.COMPLETED
    baseline.raw_sensor_summary = {"mean": 12.5}
    baseline.is_deleted = False
    return baseline


@pytest.fixture
def adapter(mock_session_factory, mock_mapper, mock_system_logger, mock_audit_logger):
    return BaselinePersistenceAdapter(
        session_factory=mock_session_factory,
        mapper=mock_mapper,
        system_logger=mock_system_logger,
        audit_logger=mock_audit_logger,
    )


def test_tc_aas_011_happy_path_save(
    adapter, valid_baseline, mock_session_factory, mock_mapper
):
    session = mock_session_factory.get_session.return_value

    result = adapter.save(valid_baseline)

    assert result == valid_baseline
    mock_mapper.to_orm_model.assert_called_once_with(valid_baseline)
    assert session.merge.call_count == 1
    assert session.commit.call_count == 1
    assert session.close.call_count == 1


def test_tc_aas_012_happy_path_delete(adapter, mock_session_factory, mock_audit_logger):
    session = mock_session_factory.get_session.return_value
    mock_record = MagicMock(spec=BaselineOrmModel)
    mock_record.is_deleted = False

    session.query.return_value.filter.return_value.first.return_value = mock_record

    result = adapter.delete("BASE-001")

    assert result is True
    assert mock_record.is_deleted is True
    assert session.commit.call_count == 1
    assert session.close.call_count == 1

    assert mock_audit_logger.log_security_event.call_count == 1
    audit_call = mock_audit_logger.log_security_event.call_args[0][0]
    assert audit_call.action == "DELETE_BASELINE"
    assert audit_call.target == "BASELINE:BASE-001"


def test_tc_aas_013_validation_failure_invalid_error_rate(
    adapter, valid_baseline, mock_session_factory
):
    valid_baseline.sync_error_rate = -0.1

    with pytest.raises(BaseSystemException) as exc_info:
        adapter.save(valid_baseline)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    mock_session_factory.get_session.assert_not_called()

    valid_baseline.sync_error_rate = 0.0800
    with pytest.raises(BaseSystemException) as exc_info_over:
        adapter.save(valid_baseline)

    assert exc_info_over.value.error_code == GlobalErrorCode.ERR_TWIN_SYNC_OVER_LIMIT


def test_tc_aas_014_db_operational_failure(
    adapter, valid_baseline, mock_session_factory
):
    session = mock_session_factory.get_session.return_value
    session.commit.side_effect = OperationalError(
        "Database disconnected", params=None, orig=Exception()
    )

    with pytest.raises(BaseSystemException) as exc_info:
        adapter.save(valid_baseline)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_DB_CONNECTION_FAILED
    assert session.rollback.call_count == 1
    assert session.close.call_count == 1


def test_tc_aas_015_delete_target_not_found(
    adapter, mock_session_factory, mock_audit_logger
):
    session = mock_session_factory.get_session.return_value
    session.query.return_value.filter.return_value.first.return_value = None

    result = adapter.delete("NON-EXISTENT-BASE")

    assert result is False
    assert session.commit.call_count == 0
    assert session.close.call_count == 1
    assert mock_audit_logger.log_security_event.call_count == 0
