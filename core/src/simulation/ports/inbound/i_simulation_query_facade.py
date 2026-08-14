from typing import Any, Protocol


class ISimulationQueryFacade(Protocol):
    def get_simulation_status(self, scenario_id: str) -> dict[str, Any]: ...
