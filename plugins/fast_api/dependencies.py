"""
===============================================================================
[File Name] dependencies.py
[Location ] /plugins/fast_api/dependencies.py
[Description]
 - FastAPI Router에서 필요한 core UseCase 및 Facade 객체를 제공하는 Dependency Injector입니다.
===============================================================================
"""

# ------------------------------------------------------------------------------
# 1. Asset Twin 서브도메인 UseCase
# ------------------------------------------------------------------------------
from plugins.jax_rl_planner.jax_rl_planner_adapter import JaxRlPlannerAdapter
from plugins.mujoco_physics.mujoco_physics_adapter import MujocoPhysicsAdapter

from core.src.asset_twin.asset_library.application.manage_asset.manage_asset_usecase import (
    ManageAssetUseCase,
)
from core.src.asset_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
)
from core.src.asset_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    ReconstructTwinUseCase,
)
from core.src.simulation.fault_injection.application.inject_fault.inject_fault_usecase import (
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
from plugins.ros2_vda5050.ros2_vda5050_deploy_adapter import Ros2Vda5050DeployAdapter

# ==============================================================================
# Simulation Outer Adapters Singleton Instances
# ==============================================================================
_physics_adapter = MujocoPhysicsAdapter()
_rl_planner_adapter = JaxRlPlannerAdapter()
_deploy_adapter = Ros2Vda5050DeployAdapter()


# ==============================================================================
# Asset Twin Dependency Injection Factory Functions
# ==============================================================================
def get_reconstruct_twin_usecase() -> ReconstructTwinUseCase:
    """
    [DI] ReconstructTwinUseCase 객체 생성 및 제공
    """
    return ReconstructTwinUseCase(
        sensor_log_parser=None,  # type: ignore
        command_repository=None,  # type: ignore
    )


def get_get_layout_usecase() -> GetLayoutUseCase:
    """
    [DI] GetLayoutUseCase 객체 생성 및 제공
    """
    return GetLayoutUseCase(query_repository=None)  # type: ignore


def get_manage_asset_usecase() -> ManageAssetUseCase:
    """
    [DI] ManageAssetUseCase 객체 생성 및 제공
    """
    return ManageAssetUseCase(command_repository=None)  # type: ignore


# ==============================================================================
# Simulation Dependency Injection Factory Functions
# ==============================================================================
def get_run_fms_simulation_usecase() -> RunFmsSimulationUseCase:
    """
    [DI] RunFmsSimulationUseCase 객체 생성 및 제공
    """
    return RunFmsSimulationUseCase(physics_engine=_physics_adapter)


def get_inject_fault_usecase() -> InjectFaultUseCase:
    """
    [DI] InjectFaultUseCase 객체 생성 및 제공
    """
    return InjectFaultUseCase(
        ai_bypass_planner=_rl_planner_adapter,
        physics_engine=_physics_adapter,
    )


def get_deploy_sim2real_usecase() -> DeploySim2RealUseCase:
    """
    [DI] DeploySim2RealUseCase 객체 생성 및 제공
    """
    return DeploySim2RealUseCase(fleet_deploy_port=_deploy_adapter)
