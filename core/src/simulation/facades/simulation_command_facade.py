from shared.context.user_context import UserContext
from simulation.fault_injection.application.inject_fault.inject_fault_dto import (
    InjectFaultRequestDto,
)
from simulation.fault_injection.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_dto import (
    RunFmsSimulationRequestDto,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)
from simulation.layout_optimization.application.optimize_layout.optimize_layout_dto import (
    OptimizeLayoutRequestDto,
)
from simulation.layout_optimization.application.optimize_layout.optimize_layout_usecase import (
    OptimizeLayoutUseCase,
)
from simulation.ports.inbound.dtos.optimized_asset_placement_dto import (
    OptimizedAssetPlacementDto,
)
from simulation.ports.inbound.dtos.sim_result_dto import SimResultDto
from simulation.ports.inbound.i_simulation_command_facade import (
    ISimulationCommandFacade,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_dto import (
    DeploySim2RealRequestDto,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_usecase import (
    DeploySim2RealUseCase,
)


class SimulationCommandFacade(ISimulationCommandFacade):
    """시뮬레이션 실행 및 배포 명령을 해당 유스케이스로 중계하는 Thin Facade"""

    def __init__(
        self,
        run_fms_uc: RunFmsSimulationUseCase,
        inject_fault_uc: InjectFaultUseCase,
        deploy_uc: DeploySim2RealUseCase,
        optimize_layout_uc: OptimizeLayoutUseCase,
    ) -> None:
        self._run_fms_uc = run_fms_uc
        self._inject_fault_uc = inject_fault_uc
        self._deploy_uc = deploy_uc
        self._optimize_layout_uc = optimize_layout_uc

    def run_fms_simulation(
        self, request_dto: RunFmsSimulationRequestDto, ctx: UserContext
    ) -> SimResultDto:
        return self._run_fms_uc.execute(request_dto=request_dto, ctx=ctx)

    def inject_fault(
        self, request_dto: InjectFaultRequestDto, ctx: UserContext
    ) -> SimResultDto:
        return self._inject_fault_uc.execute(request_dto=request_dto, ctx=ctx)

    def deploy_sim2real_package(
        self, request_dto: DeploySim2RealRequestDto, ctx: UserContext
    ) -> bool:
        return self._deploy_uc.execute(request_dto=request_dto, ctx=ctx)

    def optimize_layout(
        self, request_dto: OptimizeLayoutRequestDto, ctx: UserContext
    ) -> list[OptimizedAssetPlacementDto]:
        return self._optimize_layout_uc.execute(request_dto=request_dto, ctx=ctx)
