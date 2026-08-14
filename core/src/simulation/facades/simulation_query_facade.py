from typing import Any

from simulation.ports.inbound.i_simulation_query_facade import ISimulationQueryFacade


class SimulationQueryFacade(ISimulationQueryFacade):
    def get_simulation_status(self, scenario_id: str) -> dict[str, Any]:
        # 조회 전용 읽기 쿼리 응답
        return {
            "scenario_id": scenario_id,
            "status": "COMPLETED",
            "progress_percentage": 100.0,
        }
