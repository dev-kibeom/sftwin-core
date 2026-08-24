from typing import Protocol
from simulation.contracts.dtos.deploy_package_dto import DeployPackageDto


class IFleetDeploymentGateway(Protocol):
    """검증 완료된 배포 패키지를 실제 로봇 플릿 및 외부 제어망으로 전송하는 아웃바운드 게이트웨이 포트"""

    def deploy(self, package_dto: DeployPackageDto) -> None:
        """배포 패키지 전송 실행 (실패 시 어댑터에서 BaseSystemException 또는 OSError 발생)"""
        ...
