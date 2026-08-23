from unittest.mock import MagicMock

import pytest
from shared.context.user_context import UserContext
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.audit.audit_event_type_enum import AuditEventType
from shared.security.audit.audit_events import AuditEvent
from shared.security.audit.audit_severity_enum import AuditSeverity
from shared.security.audit.global_audit_logger import GlobalAuditLogger
from shared.security.user_role_enum import UserRole


@pytest.fixture
def mock_system_logger():
    return MagicMock(spec=GlobalSystemLogger)


@pytest.fixture
def mock_command_repo():
    return MagicMock()


def test_tc_log_01_security_event_logging_and_db_persistence(
    mock_system_logger, mock_command_repo
):
    audit_logger = GlobalAuditLogger(
        system_logger=mock_system_logger, command_repo=mock_command_repo
    )
    user_ctx = UserContext(
        user_id="usr-123",
        username="test_user",
        company_id="COMP-A",
        role=UserRole.FIELD_ENGINEER,
    )

    event = AuditEvent(
        event_type=AuditEventType.SECURITY,
        action="ACCESS_DENIED",
        target="ROBOT-ARM-01",
        severity=AuditSeverity.WARNING,
        user_ctx=user_ctx,
        trace_id="TRC-99081234a",
    )

    audit_logger.log(event)

    mock_system_logger.warn.assert_called_once()
    mock_command_repo.save.assert_called_once()


def test_tc_log_02_system_event_failsafe_user_context_fallback(
    mock_system_logger, mock_command_repo
):
    audit_logger = GlobalAuditLogger(
        system_logger=mock_system_logger, command_repo=mock_command_repo
    )

    event = AuditEvent(
        event_type=AuditEventType.FAILSAFE,
        action="ESTOP",
        target="ROBOT-ARM-01",
        severity=AuditSeverity.CRITICAL,
        details={"reason": "TORQUE_LIMIT_EXCEEDED"},
        user_ctx=None,
        trace_id="TRC-FAILSAFE-001",
    )

    audit_logger.log(event)

    mock_system_logger.error.assert_called_once()
    args = mock_system_logger.error.call_args
    log_ctx = args[0][1]

    assert log_ctx.context["user_id"] == "SYSTEM"
    assert log_ctx.context["company_id"] == "SYSTEM"
    assert log_ctx.context["target_resource"] == "ROBOT-ARM-01"


def test_tc_log_03_db_timeout_fallback_non_blocking(
    mock_system_logger, mock_command_repo
):
    mock_command_repo.save.side_effect = TimeoutError("Audit DB connection timeout!")
    audit_logger = GlobalAuditLogger(
        system_logger=mock_system_logger, command_repo=mock_command_repo
    )

    user_ctx = UserContext(
        user_id="usr-123",
        username="test_user",
        company_id="COMP-A",
        role=UserRole.FIELD_ENGINEER,
    )

    event = AuditEvent(
        event_type=AuditEventType.SECURITY,
        action="ACCESS_DENIED",
        target="ROBOT-ARM-01",
        severity=AuditSeverity.WARNING,
        user_ctx=user_ctx,
        trace_id="TRC-TIMEOUT-TEST",
    )

    try:
        audit_logger.log(event)
    except TimeoutError:
        pytest.fail("Audit DB failure must NOT raise an exception to the caller.")

    # 경고 로그(warn 1회)와 DB 실패 폴백 로그(error 1회) 검증
    mock_system_logger.warn.assert_called_once()
    mock_system_logger.error.assert_called_once()
