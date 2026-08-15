"""
Unit Test Specification for GlobalSystemLogger
"""

from shared.logger.system_logger.log_context import LogContext
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger


def test_tc_log_system_logger_json_formatting():
    logger = GlobalSystemLogger(component_name="TestComponent")
    log_ctx = LogContext(trace_id="TRC-1234", context={"service": "auth"})

    log_payload = logger.info(message="System initialisation complete", log_ctx=log_ctx)

    assert log_payload["component"] == "TestComponent"
    assert log_payload["log_level"] == "INFO"
    assert log_payload["trace_id"] == "TRC-1234"
    assert log_payload["context"]["service"] == "auth"
