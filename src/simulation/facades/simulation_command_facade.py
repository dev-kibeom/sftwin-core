"""
[File Summary]
SimulationCommandFacade
외부 API 요청 및 타 컴포넌트 통신을 위한 상태 변경 명령 진입점 (Command Facade)
"""

from typing import Any

from src.shared.dtos.sim_result_dto import SimResultDto
from src.shared.security.user_context import UserContext
from src.simulation.fms_execution.application.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)


class SimulationCommandFacade:
    def __init__(self, run_fms_uc: RunFmsSimulationUseCase):
        # UseCase 의존성 주입 (Constructor Injection)
        self._run_fms_uc = run_fms_uc

    def run_fms_simulation(
        self,
        scenario_id: str,
        baseline_id: str,
        assets: list[dict[str, Any]],
        ctx: UserContext,
    ) -> SimResultDto:
        """
        [고수준 진입점] Controller 로부터 전달받은 파라미터를 UseCase 로 위임합니다.
        """
        return self._run_fms_uc.execute(
            scenario_id=scenario_id, baseline_id=baseline_id, assets=assets, ctx=ctx
        )
