from unittest.mock import MagicMock

import pytest

from src.shared.adapters.audit_log_repository_adapter import AuditLogRepositoryAdapter
from src.shared.dtos.create_audit_log_request_dto import CreateAuditLogRequestDto
from src.shared.exceptions.base_exception import InternalServerException


def test_audit_log_repository_save_success():
    """감사 로그 저장 및 공통 감사 필드 설정 검증"""
    # Given
    adapter = AuditLogRepositoryAdapter()
    dto = CreateAuditLogRequestDto(
        trace_id="TRC-99081234a",
        component_name="EDGE_CONTROL",
        action_type="FAILSAFE_ESTOP",
        severity="CRITICAL",
        target_resource="ROBOT-ARM-01",
        details={"current_torque": 145.8},
    )

    # When
    entity = adapter.save_audit_log(dto=dto, company_id="COMP-A", created_by="usr-001")

    # Then
    assert entity.audit_id.startswith("AUD-")
    assert entity.company_id == "COMP-A"
    assert entity.created_by == "usr-001"
    assert entity.is_deleted == 0


def test_tc_shared_09_ec01_db_exception_wrapping():
    """TC-SHARED-09-EC01: DB Connection Timeout 시 예외 래핑 검증"""
    # Given
    mock_session = MagicMock()
    mock_session.is_closed = True
    adapter = AuditLogRepositoryAdapter(db_session=mock_session)

    dto = CreateAuditLogRequestDto(
        trace_id="TRC-99081234a",
        component_name="EDGE_CONTROL",
        action_type="FAILSAFE_ESTOP",
        severity="CRITICAL",
        target_resource="ROBOT-ARM-01",
    )

    # When & Then
    with pytest.raises(InternalServerException) as exc_info:
        adapter.save_audit_log(dto, company_id="COMP-A", created_by="usr-001")

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "ERR_SHARED_INTERNAL_ERROR"
