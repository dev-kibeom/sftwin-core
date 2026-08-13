# sftwin_project/dependencies.py
"""
[Global Dependency Container]
최외곽 plugins/ 컴포넌트 개발 상태에 따라 점진적으로 구현체를 주입(Plug-in)합니다.
자세한 개발 및 주입 규칙은 GTS 규약을 따릅니다.
"""

from typing import Optional

from core.src.simulation.facades.simulation_command_facade import (
    SimulationCommandFacade,
)
from core.src.simulation.fault_injection_bt.application.inject_fault_usecase import (
    InjectFaultUseCase,
)
from core.src.simulation.fms_execution.application.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)
from core.src.simulation.sim_to_real_deploy.application.deploy_sim2real_usecase import (
    DeploySim2RealUseCase,
)


class GlobalDependencyContainer:
    _instance: Optional["GlobalDependencyContainer"] = None

    def __init__(self):
        # ---------------------------------------------------------------------
        # 1. C++ Native Plugins (.so)
        # ---------------------------------------------------------------------
        # TODO(Plugin-MuJoCo): plugins/mujoco_physics 개발 완료 시 주입 활성화
        self.physics_plugin = None

        # ---------------------------------------------------------------------
        # 2. Python AI & External Services
        # ---------------------------------------------------------------------
        # TODO(Plugin-TSDB): plugins/influx_timeseries 개발 완료 시 주입 활성화
        self.tsdb_adapter = None

        # TODO(Plugin-Vision): plugins/ai_analytics 개발 완료 시 주입 활성화
        self.vision_detector = None

    @classmethod
    def get_instance(cls) -> "GlobalDependencyContainer":
        if cls._instance is None:
            cls._instance = GlobalDependencyContainer()
        return cls._instance

    def get_simulation_command_facade(self) -> SimulationCommandFacade:
        """
        현재는 core의 유즈케이스 인스턴스만 생성하여 제공하며,
        최외곽 컴포넌트가 완성되는 대로 포트에 매핑합니다.
        """
        run_fms_uc = RunFmsSimulationUseCase(
            physics_adapter=self.physics_plugin,
            # tsdb_port=self.tsdb_adapter,
        )
        inject_fault_uc = InjectFaultUseCase(
            rl_planner_adapter=None,  # TODO: RL Planner Adapter 주입 필요
            physics_adapter=self.physics_plugin,
            # vision_port=self.vision_detector
        )
        deploy_uc = DeploySim2RealUseCase(
            deploy_adapter=None
        )  # TODO: Deploy Adapter 주입 필요

        return SimulationCommandFacade(
            run_fms_uc=run_fms_uc,
            inject_fault_uc=inject_fault_uc,
            deploy_uc=deploy_uc,
        )


def get_global_sim_facade() -> SimulationCommandFacade:
    return GlobalDependencyContainer.get_instance().get_simulation_command_facade()
