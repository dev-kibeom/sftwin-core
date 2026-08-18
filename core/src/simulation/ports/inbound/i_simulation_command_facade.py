from typing import Protocol

from shared.context.user_context import UserContext
from simulation.fault_injection.application.inject_fault.inject_fault_dto import (
    InjectFaultRequestDto,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_dto import (
    RunFmsSimulationRequestDto,
)
from simulation.layout_optimization.application.optimize_layout.optimize_layout_dto import (
    OptimizeLayoutRequestDto,
)
from simulation.ports.inbound.dtos.optimized_asset_placement_dto import (
    OptimizedAssetPlacementDto,
)
from simulation.ports.inbound.dtos.sim_result_dto import SimResultDto
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_dto import (
    DeploySim2RealRequestDto,
)


class ISimulationCommandFacade(Protocol):
    def run_fms_simulation(
        self, request_dto: RunFmsSimulationRequestDto, ctx: UserContext
    ) -> SimResultDto: ...

    def inject_fault(
        self, request_dto: InjectFaultRequestDto, ctx: UserContext
    ) -> SimResultDto: ...

    def deploy_sim2real_package(
        self, request_dto: DeploySim2RealRequestDto, ctx: UserContext
    ) -> bool: ...

    def optimize_layout(
        self, request_dto: OptimizeLayoutRequestDto, ctx: UserContext
    ) -> list[OptimizedAssetPlacementDto]: ...
