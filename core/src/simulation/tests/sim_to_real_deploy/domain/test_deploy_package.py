import pytest
from simulation.sim_to_real_deploy.domain.deploy_package.deploy_package import (
    DeployPackage,
)
from simulation.sim_to_real_deploy.domain.deploy_package.deploy_package_format_enum import (
    DeployPackageFormat,
)


def test_tc_deploy_package_create_and_hash_integrity():
    """팩토리 메서드를 통한 패키지 생성 및 SHA-256 해시 무결성 검증"""
    pkg = DeployPackage.create(
        package_id="PKG-001",
        format_type=DeployPackageFormat.ROS2_WS,
        ros2_ws_path="/opt/ros/ws",
        vda5050_config={"zone": "ZONE-A"},
    )

    assert pkg.package_id == "PKG-001"
    assert pkg.format == DeployPackageFormat.ROS2_WS
    assert len(pkg.package_hash) == 64  # SHA-256 hex length
    assert pkg.verify_integrity(pkg.package_hash) is True
    assert pkg.verify_integrity("invalid_hash") is False


def test_tc_deploy_package_invariants_validation():
    """필수 필드 누락 시 예외 발생 검증"""
    with pytest.raises(ValueError, match="package_id is required"):
        DeployPackage.create(
            package_id="   ",
            format_type=DeployPackageFormat.ROS2_WS,
            ros2_ws_path="/opt/ros/ws",
        )
