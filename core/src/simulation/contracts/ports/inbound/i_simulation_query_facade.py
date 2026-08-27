from typing import Protocol

from shared.context.user_context import UserContext
from simulation.contracts.dtos.simulation_status_dto import SimulationStatusDto


class ISimulationQueryFacade(Protocol):
    def get_simulation_status(
        self, scenario_id: str, ctx: UserContext
    ) -> SimulationStatusDto: ...
