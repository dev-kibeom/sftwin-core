"""
[File Summary]
SimulationCommandFacade
외부 API 요청 및 타 컴포넌트 통신을 위한 상태 변경 명령 진입점
(FCN-SIM-001 유즈케이스에 이어 FCN-SIM-002 결함 주입 유즈케이스 연동 추가)
"""

from typing import Any

from src.shared.dtos.sim_result_dto import SimResultDto
from src.shared.security.user_context import UserContext
from src.simulation.fault_injection_bt.domain.fault_scenario import (
    FaultScenario,
    FaultTypeEnum,
)


class SimulationCommandFacade:
    def __init__(self, run_fms_uc, inject_fault_uc):
        self._run_fms_uc = run_fms_uc
        self._inject_fault_uc = inject_fault_uc  # 신규 의존성

    def run_fms_simulation(
        self,
        scenario_id: str,
        baseline_id: str,
        assets: list[dict[str, Any]],
        ctx: UserContext,
    ) -> SimResultDto:
        return self._run_fms_uc.execute(scenario_id, baseline_id, assets, ctx)

    def inject_fault(
        self, fault_type: str, target: str, bt_xml: str, ctx: UserContext
    ) -> SimResultDto:
        """
        [고수준 진입점] POST /fault-injections 컨트롤러 요청을 UseCase로 위임합니다.
        """
        scenario = FaultScenario(
            scenario_id=target,
            fault_type=FaultTypeEnum(fault_type),
            trigger_time_sec=5.0,
        )
        return self._inject_fault_uc.execute(scenario=scenario, bt_xml=bt_xml, ctx=ctx)
