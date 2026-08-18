from unittest.mock import MagicMock

import pytest
from shared.context.user_context import UserContext
from shared.enums.audit_severity_enum import AuditSeverity
from shared.enums.user_role_enum import UserRole
from shared.logger.global_audit_logger import (
    FailsafeAuditEvent,
    GlobalAuditLogger,
    SecurityAuditEvent,
)
from shared.logger.global_system_logger import GlobalSystemLogger


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

    event = SecurityAuditEvent(
        action="ACCESS_DENIED",
        target="ROBOT-ARM-01",
        severity=AuditSeverity.WARNING,
        user_ctx=user_ctx,
        trace_id="TRC-99081234a",
    )

    audit_logger.log_security_event(event)

    mock_system_logger.warn.assert_called_once()
    mock_command_repo.save.assert_called_once()


def test_tc_log_02_system_event_failsafe_user_context_fallback(
    mock_system_logger, mock_command_repo
):
    audit_logger = GlobalAuditLogger(
        system_logger=mock_system_logger, command_repo=mock_command_repo
    )

    event = FailsafeAuditEvent(
        device_id="ROBOT-ARM-01",
        action="ESTOP",
        reason="TORQUE_LIMIT_EXCEEDED",
        user_ctx=None,
        trace_id="TRC-FAILSAFE-001",
    )

    audit_logger.log_failsafe_event(event)

    mock_system_logger.error.assert_called_once()
    args = mock_system_logger.error.call_args
    log_ctx = args[0][1]

    assert log_ctx.context["user_id"] == "SYSTEM"
    assert log_ctx.context["company_id"] == "SYSTEM"


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

    event = SecurityAuditEvent(
        action="ACCESS_DENIED",
        target="ROBOT-ARM-01",
        severity=AuditSeverity.WARNING,
        user_ctx=user_ctx,
        trace_id="TRC-TIMEOUT-TEST",
    )

    try:
        audit_logger.log_security_event(event)
    except TimeoutError:
        pytest.fail("Audit DB failure must NOT raise an exception to the caller.")

    mock_system_logger.error.assert_called_once()
