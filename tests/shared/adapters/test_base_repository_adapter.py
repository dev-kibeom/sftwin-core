"""
Unit Test Specification for BaseRepositoryAdapter (TC-ADP-01, TC-ADP-04)
"""

from unittest.mock import MagicMock

import pytest

from src.shared.adapters.base_repository_adapter import BaseRepositoryAdapter
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes


class ConcreteAasRepositoryAdapter(BaseRepositoryAdapter[dict]):
    """테스트용 Concrete Repository Adapter"""

    def find_by_id(self, entity_id: str) -> dict | None:
        try:
            return self._db_session.query_id(entity_id)
        except Exception as exc:
            self._handle_driver_exception(
                exc, action_context=f"find_by_id({entity_id})"
            )

    def save(self, entity: dict) -> dict:
        return entity

    def delete(self, entity_id: str) -> bool:
        return True


# TC-ADP-01: Happy Path - Repository CRUD 및 Entity 매핑 검증
def test_tc_adp_01_repository_find_by_id_success():
    mock_session = MagicMock()
    mock_session.query_id.return_value = {"asset_id": "AAS-001", "name": "Robot Arm 01"}

    adapter = ConcreteAasRepositoryAdapter(db_session=mock_session)
    result = adapter.find_by_id("AAS-001")

    assert result == {"asset_id": "AAS-001", "name": "Robot Arm 01"}
    mock_session.query_id.assert_called_once_with("AAS-001")


# TC-ADP-04: Error Handling - DB Socket Timeout 발생 시 예외 변환 및 Wrapping 검증
def test_tc_adp_04_repository_driver_timeout_wrapping():
    mock_session = MagicMock()
    mock_session.query_id.side_effect = TimeoutError(
        "DB Driver Socket Timeout Exception!"
    )

    adapter = ConcreteAasRepositoryAdapter(db_session=mock_session)

    with pytest.raises(BaseSystemException) as exc_info:
        adapter.find_by_id("AAS-001")

    assert exc_info.value.error_code == GlobalErrorCodes.ERR_COMMON_INTERNAL_ERROR
    assert exc_info.value.status_code == 500
    assert "Database driver failure" in exc_info.value.message
