import inspect

import plugins.ros2_adapter_py as ros2_adapter_pkg
from plugins.ros2_adapter_py import (
    Ros2OutboundAdapter,
    Ros2PayloadMapper,
    Ros2ServiceClientManager,
)


class TestRos2AdapterPackageExports:
    """ROS 2 Adapter 패키지 공개 인터페이스 노출 및 계약 호환성 검증 (BDD Given-When-Then)"""

    def test_package_exports_all_symbols(self) -> None:
        """시나리오 1: plugins.ros2_adapter 패키지 공개 API 심볼 노출 검증 (Happy Path)"""
        # Given & When
        exported_symbols = getattr(ros2_adapter_pkg, "__all__", [])

        # Then
        assert "Ros2OutboundAdapter" in exported_symbols
        assert "Ros2ServiceClientManager" in exported_symbols
        assert "Ros2PayloadMapper" in exported_symbols

        assert ros2_adapter_pkg.Ros2OutboundAdapter is Ros2OutboundAdapter
        assert ros2_adapter_pkg.Ros2ServiceClientManager is Ros2ServiceClientManager
        assert ros2_adapter_pkg.Ros2PayloadMapper is Ros2PayloadMapper

    def test_ros2_outbound_adapter_method_signatures(self) -> None:
        """시나리오 2: Ros2OutboundAdapter가 Core 포트 인터페이스 계약을 준수하는지 시그니처 검증 (Contract Verification)"""
        # Given
        expected_methods = {
            "run_simulation": ["self", "scenario"],
            "plan_bypass": ["self", "obstacle_data"],
            "deploy_model_package": [
                "self",
                "target_fleet_id",
                "package_bytes",
                "expected_hash",
            ],
        }

        # When & Then
        for method_name, expected_params in expected_methods.items():
            assert hasattr(
                Ros2OutboundAdapter, method_name
            ), f"Missing method: {method_name}"
            method = getattr(Ros2OutboundAdapter, method_name)
            assert callable(method), f"{method_name} must be callable"

            sig = inspect.signature(method)
            actual_params = list(sig.parameters.keys())
            assert (
                actual_params == expected_params
            ), f"Parameter mismatch for {method_name}: expected {expected_params}, got {actual_params}"
