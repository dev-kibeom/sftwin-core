from dataclasses import dataclass


@dataclass(frozen=True)
class DeploySim2RealResultDto:
    """Sim-to-Real 배포 결과 DTO"""

    package_id: str
    package_hash: str
    is_success: bool
    deployed_at: str
