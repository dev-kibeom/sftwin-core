from unittest.mock import MagicMock

import pytest
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.persistence.base_repository import BaseRepository


class ConcreteRepository(BaseRepository[dict]):
    """드라이버 예외 변환 테스트를 위한 구체 Repository 클래스"""

    def find_by_id(self, entity_id: str) -> dict | None:
        try:
            return self._db_session.query_id(entity_id)
        except Exception as exc:
            self._handle_driver_exception(
                exc, action_context=f"find_by_id({entity_id})"
            )


@pytest.fixture
def mock_db_session():
    """저수준 DB Session Mock Fixture"""
    return MagicMock()


@pytest.fixture
def repository(mock_db_session):
    """BaseRepository 인스턴스 Fixture"""
    return ConcreteRepository(db_session=mock_db_session)


# TC-REPO-01: Happy Path - 정상 조회 시 Session 위임 검증
def test_repository_find_by_id_success(repository, mock_db_session):
    mock_db_session.query_id.return_value = {
        "asset_id": "AAS-001",
        "name": "Robot Arm 01",
    }

    result = repository.find_by_id("AAS-001")

    assert result == {"asset_id": "AAS-001", "name": "Robot Arm 01"}
    mock_db_session.query_id.assert_called_once_with("AAS-001")


# TC-REPO-02: Error Handling - 저수준 Socket Timeout 예외 포획 및 BaseSystemException 래핑 검증
def test_repository_driver_timeout_exception_translation(repository, mock_db_session):
    mock_db_session.query_id.side_effect = TimeoutError(
        "DB Driver Socket Timeout Exception!"
    )

    with pytest.raises(BaseSystemException) as exc_info:
        repository.find_by_id("AAS-001")

    assert exc_info.value.error_code == GlobalErrorCodeEnum.ERR_COMMON_INTERNAL_ERROR
    assert exc_info.value.status_code == 500
    assert "Database driver failure encountered" in exc_info.value.message
    assert exc_info.value.details.get("original_exception") == "TimeoutError"
