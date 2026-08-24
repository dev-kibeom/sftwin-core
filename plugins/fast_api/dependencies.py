"""
===============================================================================
[File Name] dependencies.py
[Location ] /plugins/fast_api/dependencies.py
[Description]
 - FastAPI Router에서 필요한 core UseCase 및 Facade 객체를 제공하는 통합 Dependency Injector입니다.
===============================================================================
"""

# ------------------------------------------------------------------------------
# 1. Asset Twin 서브도메인 UseCase
# ------------------------------------------------------------------------------
from digital_twin.asset_library.application.register_asset.register_asset_usecase import (
    ManageAssetUseCase,
)
from kpi_b2b.b2b_procurement.application.create_expert_session.create_expert_session_usecase import (
    LayoutMirroringUseCase,
)
from shared.security.rbac_authorization_manager import RbacAuthorizationManager

from core.src.digital_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
)
from core.src.digital_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    ReconstructTwinUseCase,
)
from core.src.kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from core.src.kpi_b2b.b2b_procurement.application.process_production_order.process_production_order_usecase import (
    ProcessProductionOrderUseCase,
)
from core.src.kpi_b2b.facades.kpi_query_facade import KpiQueryFacade
from core.src.kpi_b2b.facades.procurement_command_facade import ProcurementCommandFacade

# ------------------------------------------------------------------------------
# 3. KPI & B2B Procurement 서브도메인 UseCase, Facade & Security
# ------------------------------------------------------------------------------
from core.src.kpi_b2b.kpi_dashboard.application.calculate_kpi.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from core.src.kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_usecase import (
    GenerateDualKpiReportUseCase,
)
from core.src.simulation.fault_recovery.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)

# ------------------------------------------------------------------------------
# 2. Simulation 서브도메인 UseCase & Outer Plugin Adapters
# ------------------------------------------------------------------------------
from core.src.simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)
from core.src.simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_usecase import (
    DeploySim2RealUseCase,
)
from plugins.jax_rl_planner.jax_rl_planner_adapter import JaxRlPlannerAdapter
from plugins.mujoco_physics.mujoco_physics_adapter import MujocoPhysicsAdapter
from plugins.ros2_vda5050.ros2_vda5050_deploy_adapter import Ros2Vda5050DeployAdapter

# ==============================================================================
# Simulation Outer Adapters Singleton Instances
# ==============================================================================
_physics_adapter = MujocoPhysicsAdapter()
_rl_planner_adapter = JaxRlPlannerAdapter()
_deploy_adapter = Ros2Vda5050DeployAdapter()

# ==============================================================================
# KPI & B2B Common Singleton Instances (RBAC, Stub Repositories)
# ==============================================================================
_rbac_manager = RbacAuthorizationManager()
_kpi_query_repo_stub = None
_procurement_command_repo_stub = None
_procurement_query_repo_stub = None


# ==============================================================================
# 1. Asset Twin DI Factory Functions
# ==============================================================================
def get_reconstruct_twin_usecase() -> ReconstructTwinUseCase:
    return ReconstructTwinUseCase(
        sensor_log_parser=None,  # type: ignore
        command_repository=None,  # type: ignore
    )


def get_get_layout_usecase() -> GetLayoutUseCase:
    return GetLayoutUseCase(query_repository=None)  # type: ignore


def get_manage_asset_usecase() -> ManageAssetUseCase:
    return ManageAssetUseCase(command_repository=None)  # type: ignore


# ==============================================================================
# 2. Simulation DI Factory Functions
# ==============================================================================
def get_run_fms_simulation_usecase() -> RunFmsSimulationUseCase:
    return RunFmsSimulationUseCase(physics_engine=_physics_adapter)


def get_inject_fault_usecase() -> InjectFaultUseCase:
    return InjectFaultUseCase(
        ai_bypass_planner=_rl_planner_adapter,
        physics_engine=_physics_adapter,
    )


def get_deploy_sim2real_usecase() -> DeploySim2RealUseCase:
    return DeploySim2RealUseCase(fleet_deploy_port=_deploy_adapter)


# ==============================================================================
# 3. KPI & B2B Procurement DI Factory Functions
# ==============================================================================
def get_calculate_kpi_usecase() -> CalculateKpiUseCase:
    return CalculateKpiUseCase(query_repo=_kpi_query_repo_stub)  # type: ignore


def get_generate_dual_kpi_report_usecase() -> GenerateDualKpiReportUseCase:
    return GenerateDualKpiReportUseCase()


def get_kpi_facade() -> KpiQueryFacade:
    return KpiQueryFacade(
        calculate_kpi_uc=get_calculate_kpi_usecase(),
        dual_kpi_uc=get_generate_dual_kpi_report_usecase(),
        rbac_manager=_rbac_manager,
        sim_repo=_kpi_query_repo_stub,
    )


def get_generate_quote_usecase() -> GenerateQuoteUseCase:
    return GenerateQuoteUseCase(command_repo=_procurement_command_repo_stub)  # type: ignore


def get_layout_mirroring_usecase() -> LayoutMirroringUseCase:
    return LayoutMirroringUseCase(command_repo=_procurement_command_repo_stub)  # type: ignore


def get_process_production_order_usecase() -> ProcessProductionOrderUseCase:
    return ProcessProductionOrderUseCase(inventory_repo=None)  # type: ignore


def get_procurement_facade() -> ProcurementCommandFacade:
    return ProcurementCommandFacade(
        generate_quote_uc=get_generate_quote_usecase(),
        mirroring_uc=get_layout_mirroring_usecase(),
        command_repo=_procurement_command_repo_stub,  # type: ignore
        query_repo=_procurement_query_repo_stub,  # type: ignore
        rbac_manager=_rbac_manager,
    )
