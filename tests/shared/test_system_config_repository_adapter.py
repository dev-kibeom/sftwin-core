from src.shared.adapters.system_config_repository_adapter import (
    SystemConfigRepositoryAdapter,
)


def test_repository_adapter_find_by_key_success():
    """SystemConfigRepositoryAdapter 키 조회 성공 검증"""
    adapter = SystemConfigRepositoryAdapter()
    entity = adapter.find_by_key("EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS")

    assert entity is not None
    assert entity.config_key == "EDGE_FAILSAFE_HEARTBEAT_TIMEOUT_MS"
    assert entity.config_value == "100"
    assert entity.is_deleted == 0


def test_repository_adapter_find_deleted_key_returns_none():
    """논리 삭제(is_deleted=1)된 키 조회 시 None 반환 검증"""
    adapter = SystemConfigRepositoryAdapter()
    entity = adapter.find_by_key("DELETED_CONFIG_KEY")

    assert entity is None, "is_deleted=1 항목은 None을 반환해야 합니다."
