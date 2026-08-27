# File: sftwin_project/core/src/simulation/facades/simulation_query_facade.py

from shared.context.user_context import UserContext
from shared.enums.simulation_state_enum import SimulationState
from shared.security.context_guard import require_permission
from shared.security.user_role_enum import UserRole
from simulation.contracts.dtos.simulation_status_dto import SimulationStatusDto
from simulation.contracts.ports.inbound.i_simulation_query_facade import (
    ISimulationQueryFacade,
)


class SimulationQueryFacade(ISimulationQueryFacade):
    @require_permission(UserRole.CREATOR, "SIM_GET_STATUS")
    def get_simulation_status(
        self, scenario_id: str, ctx: UserContext
    ) -> SimulationStatusDto:
        return SimulationStatusDto(
            scenario_id=scenario_id,
            status=SimulationState.COMPLETED,
            progress_percent=100.0,
            current_step="Execution completed",
            execution_details={"company_id": ctx.company_id},
        )
