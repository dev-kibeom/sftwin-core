from typing import Any, Protocol


class IFleetDeploy(Protocol):
    """
    검증 완료된 배포 패키지를 파일 시스템/에지로 추출하는 아웃바운드 포트
    """

    def export_package(self, package_entity: Any) -> bool: ...
