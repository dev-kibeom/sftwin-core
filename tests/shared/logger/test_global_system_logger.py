"""
Unit Test Specification for GlobalSystemLogger and AuditLogger
"""

from unittest.mock import MagicMock

from src.shared.logging.global_system_logger import AuditLogger, GlobalSystemLogger
from src.shared.security.rbac_authorization_manager import AuditSeverityEnum
from src.shared.security.user_context import UserContext, UserRoleEnum


def test_global_system_logger_json_format():
    logger = GlobalSystemLogger(component_name="TestComponent")
    log_payload = logger.log_structured_event(
        level="INFO",
        message="Test structured log",
        context={"key": "value"},
        trace_id="TRC-TEST-123",
    )

    assert log_payload["component"] == "TestComponent"
    assert log_payload["log_level"] == "INFO"
    assert log_payload["trace_id"] == "TRC-TEST-123"
    assert log_payload["context"]["key"] == "value"


def test_audit_logger_security_event_formatting():
    mock_system_logger = MagicMock(spec=GlobalSystemLogger)
    audit_logger = AuditLogger(system_logger=mock_system_logger)

    user_ctx = UserContext(
        user_id="usr-99",
        username="tester",
        company_id="COMP-XYZ",
        role=UserRoleEnum.FIELD_ENGINEER,
    )

    audit_logger.log_security_event(
        user_ctx=user_ctx,
        action="ACCESS_DENIED",
        target="SECRET_ASSET",
        severity=AuditSeverityEnum.WARNING,
        trace_id="TRC-AUDIT-999",
    )

    mock_system_logger.log_structured_event.assert_called_once()
    kwargs = mock_system_logger.log_structured_event.call_args.kwargs
    assert kwargs["level"] == "WARN"
    assert kwargs["trace_id"] == "TRC-AUDIT-999"
    assert kwargs["context"]["user_id"] == "usr-99"
    assert kwargs["context"]["action"] == "ACCESS_DENIED"
