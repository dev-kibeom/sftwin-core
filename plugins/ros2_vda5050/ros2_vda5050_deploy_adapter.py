from typing import Any

from simulation.ports.outbound.i_fleet_deploy import IFleetDeploy


class Ros2Vda5050DeployAdapter(IFleetDeploy):
    """
    ROS2 런치 파일, 파라미터(YAML) 및 VDA 5050 표준 규격 파일 추출 구체 어댑터
    """

    def export_package(self, package_entity: Any) -> bool:
        # TODO: os/shutil 모듈을 사용한 파일 시스템 추출 로직 구현
        return True
