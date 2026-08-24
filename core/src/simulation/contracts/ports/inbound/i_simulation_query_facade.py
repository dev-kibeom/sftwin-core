from typing import Any, Protocol

from shared.context.user_context import UserContext


class ISimulationQueryFacade(Protocol):
    def get_simulation_status(
        self, scenario_id: str, ctx: UserContext
    ) -> dict[str, Any]: ...
