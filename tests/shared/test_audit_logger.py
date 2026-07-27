from unittest.mock import MagicMock

from src.shared.logging.audit_logger import AuditLogger


def test_tc_shared_06_hp01_audit_logger_failsafe_event():
    """TC-SHARED-06-HP01: AuditLogger Failsafe 이벤트 구조화 로깅 검증"""
    # Given
    mock_system_logger = MagicMock()
    audit_logger = AuditLogger(system_logger=mock_system_logger)

    # When
    audit_logger.log_failsafe_event(
        device_id="ROBOT-ARM-01",
        action="FAILSAFE_ESTOP",
        reason="TORQUE_LIMIT_EXCEEDED",
        trace_id="TRC-99081234a",
    )

    # Then
    mock_system_logger.error.assert_called_once()
    kwargs = mock_system_logger.error.call_args.kwargs
    assert kwargs["trace_id"] == "TRC-99081234a"
    assert kwargs["component"] == "EdgeControlComponent"
    assert kwargs["context"]["device_id"] == "ROBOT-ARM-01"
    assert kwargs["context"]["failsafe_action"] == "FAILSAFE_ESTOP"
