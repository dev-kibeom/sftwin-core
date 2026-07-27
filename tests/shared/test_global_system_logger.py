import json

from src.shared.logging.global_system_logger import GlobalSystemLogger


def test_tc_shared_06_structured_json_formatting():
    """GlobalSystemLogger의 JSON 구조화 포맷 출력 검증"""
    # Given
    logger = GlobalSystemLogger("test_logger")

    # When
    log_json_str = logger._format_structured_json(
        level="INFO",
        message="System started",
        trace_id="TRC-1234",
        component="TestComponent",
        context={"key": "value"},
    )
    parsed = json.loads(log_json_str)

    # Then
    assert parsed["log_level"] == "INFO"
    assert parsed["message"] == "System started"
    assert parsed["trace_id"] == "TRC-1234"
    assert parsed["component"] == "TestComponent"
    assert parsed["context"]["key"] == "value"
