"""
[File Summary]
Ros2Vda5050DeployAdapter
도메인에서 생성된 설정값을 바탕으로 실제 ROS2 런치 파일, 파라미터(YAML) 및 표준 패키지를 파일 시스템에 쓰는 구체 어댑터입니다.
"""

from simulation.sim_to_real_deploy.domain.deploy_package import DeployPackage


class Ros2Vda5050DeployAdapter:
    def export_package(self, pkg: DeployPackage) -> bool:
        """
        지정된 포맷(ROS2_WS, VDA_5050 등)에 따라 패키지를 추출합니다.
        (실제 환경에서는 os, shutil 등을 사용하여 파일 I/O를 수행하며, 단위 테스트 시 모킹됩니다)
        """
        # I/O 작업을 모사
        # if not os.path.exists(pkg.ros2_ws_path): ...
        return True
