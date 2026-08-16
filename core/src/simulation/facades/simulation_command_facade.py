from typing import Any

from shared.dtos.sim_result_dto import SimResultDto
from shared.context.user_context import UserContext

from simulation.fault_injection.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)
from simulation.fault_injection.domain.fault_scenario import (
    FaultScenario,
    FaultTypeEnum,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)
from simulation.ports.inbound.i_simulation_command_facade import (
    ISimulationCommandFacade,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_usecase import (
    DeploySim2RealUseCase,
)


class SimulationCommandFacade(ISimulationCommandFacade):
    def __init__(
        self,
        run_fms_uc: RunFmsSimulationUseCase,
        inject_fault_uc: InjectFaultUseCase,
        deploy_uc: DeploySim2RealUseCase,
    ):
        self._run_fms_uc = run_fms_uc
        self._inject_fault_uc = inject_fault_uc
        self._deploy_uc = deploy_uc

    def run_fms_simulation(
        self,
        scenario_id: str,
        baseline_id: str,
        assets: list[dict[str, Any]],
        ctx: UserContext,
    ) -> SimResultDto:
        return self._run_fms_uc.execute(scenario_id, baseline_id, assets, ctx)

    def inject_fault(
        self,
        fault_type: str,
        target: str,
        sequence_script: str,
        ctx: UserContext,
    ) -> SimResultDto:
        scenario = FaultScenario(
            scenario_id=target,
            fault_type=FaultTypeEnum(fault_type),
            trigger_time_sec=5.0,
        )
        return self._inject_fault_uc.execute(
            scenario=scenario, sequence_script=sequence_script, ctx=ctx
        )

    def deploy_sim2real_package(
        self,
        package_id: str,
        format_type: str,
        config: dict[str, Any],
        ctx: UserContext,
    ) -> bool:
        return self._deploy_uc.execute(
            package_id=package_id, format_type=format_type, config=config, ctx=ctx
        )
