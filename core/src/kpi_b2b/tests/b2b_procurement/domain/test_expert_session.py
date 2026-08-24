import pytest
from kpi_b2b.b2b_procurement.domain.expert_session.expert_session import (
    ExpertSession,
)
from kpi_b2b.b2b_procurement.domain.expert_session.expert_session_status_enum import (
    ExpertSessionStatus,
)


def test_tc_expert_session_factory_create_success():
    """팩토리 메서드를 통한 세션 생성 및 초기 상태/속성 검증"""
    session = ExpertSession.create(
        baseline_id="BASE-001",
        expires_in_seconds=7200,
    )

    assert session.session_id.startswith("SESS-")
    assert session.session_token.startswith("TKN-")
    assert session.baseline_id == "BASE-001"
    assert session.expert_id == "UNASSIGNED"
    assert session.status == ExpertSessionStatus.WAITING
    assert session.expires_in_seconds == 7200


def test_tc_expert_session_assign_expert_lifecycle():
    """전문가 배정 시 ACTIVE 전이 및 종료 시 CLOSED 전이 검증"""
    session = ExpertSession.create(baseline_id="BASE-001")

    # 1. 전문가 배정 (WAITING -> ACTIVE)
    session.assign_expert(expert_id="EXPERT-999")
    assert session.expert_id == "EXPERT-999"
    assert session.status == ExpertSessionStatus.ACTIVE

    # 2. 세션 정상 종료 (ACTIVE -> CLOSED)
    session.close()
    assert session.status == ExpertSessionStatus.CLOSED

    # 3. 이미 종료된 세션에 대한 재종료 시도 예외 검증
    with pytest.raises(ValueError, match="already closed"):
        session.close()


def test_tc_expert_session_invalid_state_transition():
    """유효하지 않은 상태에서 전문가 배정 시도 시 예외 검증"""
    session = ExpertSession.create(baseline_id="BASE-001")
    session.close()

    with pytest.raises(ValueError, match="Cannot assign expert"):
        session.assign_expert(expert_id="EXPERT-999")


def test_tc_expert_session_validation_invariants():
    """필수 필드 및 유효시간 도메인 불변식 검증"""
    with pytest.raises(ValueError, match="Valid session_id"):
        ExpertSession(
            session_id="",
            baseline_id="BASE-01",
            session_token="TKN-01",
        )

    with pytest.raises(ValueError, match="Valid baseline_id"):
        ExpertSession(
            session_id="SESS-01",
            baseline_id="   ",
            session_token="TKN-01",
        )

    with pytest.raises(ValueError, match="expires_in_seconds"):
        ExpertSession(
            session_id="SESS-01",
            baseline_id="BASE-01",
            session_token="TKN-01",
            expires_in_seconds=0,
        )
