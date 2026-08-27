# File: sftwin_project/core/src/simulation/facades/simulation_command_facade.py

from digital_twin.contracts.dtos.asset_dto import AssetDto
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.context_guard import require_permission
from shared.security.user_role_enum import UserRole
from simulation.contracts.dtos.optimized_asset_placement_dto import (
    OptimizedAssetPlacementDto,
)
from simulation.contracts.dtos.sim_result_dto import SimResultDto
from simulation.contracts.ports.inbound.i_simulation_command_facade import (
    ISimulationCommandFacade,
)
from simulation.fault_recovery.application.fault_recovery_scenario.fault_recovery_scenario_usecase import (
    SimulateFaultRecoveryScenarioUseCase,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_request_dto import (
    InjectFaultRequestDto,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_result_dto import (
    InjectFaultResultDto,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_request_dto import (
    RunFmsSimulationRequestDto,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)
from simulation.layout_optimization.application.optimize_layout.optimize_layout_request_dto import (
    OptimizeLayoutRequestDto,
)
from simulation.layout_optimization.application.optimize_layout.optimize_layout_usecase import (
    OptimizeLayoutUseCase,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_request_dto import (
    DeploySim2RealRequestDto,
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
        optimize_layout_uc: OptimizeLayoutUseCase,
        fault_recovery_scenario_uc: SimulateFaultRecoveryScenarioUseCase | None = None,
    ) -> None:
        self._run_fms_uc = run_fms_uc
        self._inject_fault_uc = inject_fault_uc
        self._deploy_uc = deploy_uc
        self._optimize_layout_uc = optimize_layout_uc
        self._fault_recovery_scenario_uc = fault_recovery_scenario_uc

    @require_permission(UserRole.FIELD_ENGINEER, "SIM_RUN_FMS")
    def run_fms_simulation(
        self, request_dto: RunFmsSimulationRequestDto, ctx: UserContext
    ) -> SimResultDto:
        return self._run_fms_uc.execute(request_dto=request_dto, ctx=ctx)

    @require_permission(UserRole.FIELD_ENGINEER, "SIM_INJECT_FAULT")
    def inject_fault(
        self, request_dto: InjectFaultRequestDto, ctx: UserContext
    ) -> InjectFaultResultDto:
        return self._inject_fault_uc.execute(request_dto=request_dto, ctx=ctx)

    @require_permission(UserRole.FIELD_ENGINEER, "SIM_FAULT_RECOVERY_SCENARIO")
    def simulate_fault_recovery_scenario(
        self,
        fault_request_dto: InjectFaultRequestDto,
        sequence_script: str,
        assets: tuple[AssetDto, ...],
        ctx: UserContext,
    ) -> SimResultDto:
        if not self._fault_recovery_scenario_uc:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                custom_message="SimulateFaultRecoveryScenarioUseCase is not configured in SimulationCommandFacade.",
            )
        return self._fault_recovery_scenario_uc.execute(
            fault_request_dto=fault_request_dto,
            sequence_script=sequence_script,
            assets=assets,
            ctx=ctx,
        )

    @require_permission(UserRole.FACTORY_MANAGER, "SIM_DEPLOY_SIM2REAL")
    def deploy_sim2real_package(
        self, request_dto: DeploySim2RealRequestDto, ctx: UserContext
    ) -> bool:
        res = self._deploy_uc.execute(request_dto=request_dto, ctx=ctx)
        return res.is_success

    @require_permission(UserRole.CREATOR, "SIM_OPTIMIZE_LAYOUT")
    def optimize_layout(
        self, request_dto: OptimizeLayoutRequestDto, ctx: UserContext
    ) -> list[OptimizedAssetPlacementDto]:
        return self._optimize_layout_uc.execute(request_dto=request_dto, ctx=ctx)
