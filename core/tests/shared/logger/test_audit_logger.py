"""
Unit Test Specification for FEAT-SHARED-03
"""

from unittest.mock import MagicMock

import pytest

from src.shared.dtos.audit_dtos import FailsafeAuditEvent, SecurityAuditEvent
from src.shared.logger.audit_logger import AuditLogger, AuditSeverityEnum
from src.shared.logger.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext, UserRoleEnum


@pytest.fixture
def mock_system_logger():
    return MagicMock(spec=GlobalSystemLogger)


@pytest.fixture
def mock_db_session():
    return MagicMock()


def test_tc_log_01_security_event_logging_and_db_persistence(
    mock_system_logger, mock_db_session
):
    audit_logger = AuditLogger(
        system_logger=mock_system_logger, db_session=mock_db_session
    )
    user_ctx = UserContext(
        user_id="usr-123",
        username="test_user",
        company_id="COMP-A",
        role=UserRoleEnum.FIELD_ENGINEER,
    )

    event = SecurityAuditEvent(
        action="ACCESS_DENIED",
        target="ROBOT-ARM-01",
        severity=AuditSeverityEnum.WARNING,
        user_ctx=user_ctx,
        trace_id="TRC-99081234a",
    )

    audit_logger.log_security_event(event)

    mock_system_logger._format_and_dispatch.assert_called_once()
    args = mock_system_logger._format_and_dispatch.call_args
    level = args[0][0]
    log_ctx = args[0][2]

    assert level == "WARN"
    assert log_ctx.trace_id == "TRC-99081234a"
    assert log_ctx.context["user_id"] == "usr-123"

    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_tc_log_02_system_event_failsafe_user_context_fallback(
    mock_system_logger, mock_db_session
):
    audit_logger = AuditLogger(
        system_logger=mock_system_logger, db_session=mock_db_session
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
    mock_system_logger, mock_db_session
):
    mock_db_session.execute.side_effect = TimeoutError("Audit DB connection timeout!")
    audit_logger = AuditLogger(
        system_logger=mock_system_logger, db_session=mock_db_session
    )

    user_ctx = UserContext(
        user_id="usr-123",
        username="test_user",
        company_id="COMP-A",
        role=UserRoleEnum.FIELD_ENGINEER,
    )

    event = SecurityAuditEvent(
        action="ACCESS_DENIED",
        target="ROBOT-ARM-01",
        severity=AuditSeverityEnum.WARNING,
        user_ctx=user_ctx,
        trace_id="TRC-TIMEOUT-TEST",
    )

    try:
        audit_logger.log_security_event(event)
    except TimeoutError:
        pytest.fail("Audit DB failure must NOT raise an exception to the caller.")

    mock_system_logger.error.assert_called_once()
    call_args = mock_system_logger.error.call_args
    msg = call_args.kwargs.get("message") or (call_args[0][0] if call_args[0] else "")

    assert "Audit DB Persist Fallback" in msg
