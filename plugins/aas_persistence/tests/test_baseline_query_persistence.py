from decimal import Decimal
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
    return MagicMock()


@pytest.fixture
def adapter(mock_session_factory, mock_mapper, mock_system_logger, mock_audit_logger):
    return BaselinePersistenceAdapter(
        session_factory=mock_session_factory,
        mapper=mock_mapper,
        system_logger=mock_system_logger,
        audit_logger=mock_audit_logger,
    )


@pytest.fixture
def sample_baseline_orm_model():
    return BaselineOrmModel(
        baseline_id="BASE-001",
        company_id="COMP-A",
        baseline_name="Baseline_Model_X1",
        sync_error_rate=Decimal("0.0350"),
        sync_status="COMPLETED",
        raw_sensor_summary={"mean": 12.5},
        is_deleted=False,
    )


def test_tc_aas_016_happy_path_found(
    adapter, mock_session_factory, mock_mapper, sample_baseline_orm_model
):
    session = mock_session_factory.get_session.return_value
    session.query.return_value.filter.return_value.first.return_value = (
        sample_baseline_orm_model
    )

    mock_domain_baseline = MagicMock(spec=TwinBaseline)
    mock_mapper.to_domain_entity.return_value = mock_domain_baseline

    result = adapter.find_by_id("BASE-001")

    assert result == mock_domain_baseline
    assert session.close.call_count == 1
    mock_mapper.to_domain_entity.assert_called_once_with(sample_baseline_orm_model)


def test_tc_aas_017_not_found(adapter, mock_session_factory, mock_mapper):
    session = mock_session_factory.get_session.return_value
    session.query.return_value.filter.return_value.first.return_value = None

    result = adapter.find_by_id("NON-EXISTENT-BASE")

    assert result is None
    assert session.close.call_count == 1
    mock_mapper.to_domain_entity.assert_not_called()


def test_tc_aas_018_db_operational_failure(adapter, mock_session_factory):
    session = mock_session_factory.get_session.return_value
    session.query.return_value.filter.side_effect = OperationalError(
        "DB connection lost", params=None, orig=Exception()
    )

    with pytest.raises(BaseSystemException) as exc_info:
        adapter.find_by_id("BASE-001")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_DB_CONNECTION_FAILED
    assert session.rollback.call_count == 1
    assert session.close.call_count == 1
