# contracts/ports/outbound/i_recovery_script_loader.py
from typing import Protocol

from simulation.fault_recovery.domain.recovery_sequence.recovery_sequence import (
    RecoverySequence,
)


class IRecoveryScriptLoader(Protocol):
    """우회/복구 BehaviorTree 스크립트를 로드하고 구문 검증된 도메인 객체로 반환하는 포트"""

    def load_and_validate(self, script_id_or_content: str) -> RecoverySequence | None:
        """스크립트를 조회하고 XML/YAML 문법을 검증하여 도메인 VO로 반환 (실패/미존재 시 None 반환)"""
        ...
