from unittest.mock import MagicMock

import pytest

from src.shared.exceptions.base_exception import ConfigNotFoundException
from src.shared.ports.system_config_repository import (
    SystemConfigEntity,
    SystemConfigRepository,
)
from src.shared.services.system_config_service import SystemConfigService


def test_system_config_service_get_config_success():
    """SystemConfigService 정상 조회 및 DTO 매핑 검증"""
    # Given
    mock_repo = MagicMock(spec=SystemConfigRepository)
    mock_entity = SystemConfigEntity(
        config_key="EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS",
        config_value="100",
        description="Heartbeat timeout",
        updated_at="2026-07-27T12:00:00Z",
        is_deleted=0,
    )
    mock_repo.find_by_key.return_value = mock_entity

    service = SystemConfigService(repository=mock_repo)

    # When
    dto = service.get_config("EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS")

    # Then
    assert dto.config_key == "EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS"
    assert dto.config_value == "100"
    assert dto.description == "Heartbeat timeout"
    assert dto.updated_at == "2026-07-27T12:00:00Z"


def test_tc_shared_08_ec01_service_raises_config_not_found():
    """TC-SHARED-08-EC01: 미존재/삭제 키 조회 시 ConfigNotFoundException 던짐 검증"""
    # Given
    mock_repo = MagicMock(spec=SystemConfigRepository)
    mock_repo.find_by_key.return_value = None

    service = SystemConfigService(repository=mock_repo)

    # When & Then
    with pytest.raises(ConfigNotFoundException) as exc_info:
        service.get_config("INVALID_CONFIG_KEY")

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "ERR_SHARED_CONFIG_NOT_FOUND"
    assert (
        exc_info.value.message == "Requested system configuration key does not exist."
    )
