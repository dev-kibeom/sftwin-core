from typing import Any

from shared.context.user_context import UserContext
from simulation.contracts.ports.inbound.i_simulation_query_facade import (
    ISimulationQueryFacade,
)


class SimulationQueryFacade(ISimulationQueryFacade):
    def get_simulation_status(
        self, scenario_id: str, ctx: UserContext
    ) -> dict[str, Any]:
        # 조회 전용 읽기 쿼리 응답 (멀티테넌트 컨텍스트 추적)
        return {
            "scenario_id": scenario_id,
            "company_id": ctx.company_id,
            "status": "COMPLETED",
            "progress_percentage": 100.0,
        }
