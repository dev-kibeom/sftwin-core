from typing import Protocol

from simulation.sim_to_real_deploy.domain.deploy_package.deploy_package import (
    DeployPackage,
)


class IFleetDeploy(Protocol):
    """검증 완료된 배포 패키지를 파일 시스템 또는 실제 로봇 플릿으로 전송하는 아웃바운드 포트"""

    def export_package(self, package: DeployPackage) -> bool: ...
