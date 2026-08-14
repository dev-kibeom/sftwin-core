from typing import Any, Protocol


class ISimulationCommandFacade(Protocol):
    def run_fms_simulation(
        self, scenario_id: str, baseline_id: str, assets: list[dict[str, Any]], ctx: Any
    ) -> Any: ...

    def inject_fault(
        self, fault_type: str, target: str, sequence_script: str, ctx: Any
    ) -> Any: ...

    def deploy_sim2real_package(
        self, package_id: str, format_type: str, config: dict[str, Any], ctx: Any
    ) -> bool: ...
