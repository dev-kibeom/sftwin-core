from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode

from plugins.ros2_adapter_py.clients.ros2_service_client_manager import (
    Ros2ServiceClientManager,
)


class TestRos2ServiceClientManager:
    """Ros2ServiceClientManager 단위 테스트 (BDD Given-When-Then)"""

    @pytest.fixture
    def mock_node(self) -> MagicMock:
        """rclpy.node.Node 모의 객체 Fixture"""
        node = MagicMock()
        node.create_client.return_value = MagicMock()
        node.create_publisher.return_value = MagicMock()
        return node

    def _setup_mock_future(
        self,
        mock_client: MagicMock,
        response: Any = None,
        exception: Exception | None = None,
    ) -> MagicMock:
        """성공/실패 콜백을 즉시 트리거하는 Mock Future 헬퍼"""
        mock_future = MagicMock()
        mock_future.result.return_value = response
        mock_future.exception.return_value = exception
        mock_future.add_done_callback.side_effect = lambda cb: cb(mock_future)
        mock_client.call_async.return_value = mock_future
        return mock_future

    def test_call_simulate_scenario_success(self, mock_node: MagicMock) -> None:
        """시나리오 1: SimulateScenario 서비스 정상 호출 및 응답 검증 (Happy Path)"""
        # Given
        manager = Ros2ServiceClientManager(node=mock_node)
        request = SimpleNamespace(scenario_id="SCENARIO_001")
        expected_response = SimpleNamespace(success=True, trajectory_points=[])

        mock_client = manager._sim_client
        mock_client.wait_for_service.return_value = True
        self._setup_mock_future(mock_client, response=expected_response)

        # When
        response = manager.call_simulate_scenario(request, timeout_sec=10.0)

        # Then
        mock_client.wait_for_service.assert_called_with(timeout_sec=2.0)
        mock_client.call_async.assert_called_once_with(request)
        assert response == expected_response

    def test_call_plan_amr_bypass_success(self, mock_node: MagicMock) -> None:
        """시나리오 2-1: PlanAmrBypass 서비스 정상 호출 검증 (Happy Path)"""
        # Given
        manager = Ros2ServiceClientManager(node=mock_node)
        request = SimpleNamespace(robot_id="AMR_001")
        expected_response = SimpleNamespace(success=True, trajectory_points=[])

        mock_client = manager._amr_bypass_client
        mock_client.wait_for_service.return_value = True
        self._setup_mock_future(mock_client, response=expected_response)

        # When
        response = manager.call_plan_amr_bypass(request, timeout_sec=3.0)

        # Then
        mock_client.call_async.assert_called_once_with(request)
        assert response == expected_response

    def test_call_plan_arm_trajectory_success(self, mock_node: MagicMock) -> None:
        """시나리오 2-2: PlanManipulatorTrajectory 서비스 정상 호출 검증 (Happy Path)"""
        # Given
        manager = Ros2ServiceClientManager(node=mock_node)
        request = SimpleNamespace(asset_id="ROBOT_001")
        expected_response = SimpleNamespace(success=True, trajectory_points=[])

        mock_client = manager._arm_plan_client
        mock_client.wait_for_service.return_value = True
        self._setup_mock_future(mock_client, response=expected_response)

        # When
        response = manager.call_plan_arm_trajectory(request, timeout_sec=3.0)

        # Then
        mock_client.call_async.assert_called_once_with(request)
        assert response == expected_response

    def test_call_update_planning_scene_success(self, mock_node: MagicMock) -> None:
        """시나리오 2-3: UpdatePlanningScene 서비스 정상 호출 검증 (Happy Path)"""
        # Given
        manager = Ros2ServiceClientManager(node=mock_node)
        request = SimpleNamespace(obstacles=[])
        expected_response = SimpleNamespace(success=True)

        mock_client = manager._scene_client
        mock_client.wait_for_service.return_value = True
        self._setup_mock_future(mock_client, response=expected_response)

        # When
        response = manager.call_update_planning_scene(request, timeout_sec=3.0)

        # Then
        mock_client.call_async.assert_called_once_with(request)
        assert response == expected_response

    def test_publish_estop_success(self, mock_node: MagicMock) -> None:
        """시나리오 3: E-Stop 토픽 메시지 발행 검증 (Failsafe Broadcast)"""
        # Given
        manager = Ros2ServiceClientManager(node=mock_node)

        # When
        manager.publish_estop(
            action_type="ESTOP", trigger_reason="CORE_FAILSAFE_TRIGGERED"
        )

        # Then
        assert manager._estop_publisher.publish.called
        published_msg = manager._estop_publisher.publish.call_args[0][0]
        assert getattr(published_msg, "action_type", None) == "ESTOP"
        assert (
            getattr(published_msg, "trigger_reason", None) == "CORE_FAILSAFE_TRIGGERED"
        )

    def test_service_unavailable_raises_dds_init_fail(
        self, mock_node: MagicMock
    ) -> None:
        """시나리오 4: 서비스 서버 미구동/연결 실패 시 ERR_EDGE_DDS_INIT_FAIL 예외 검증"""
        # Given
        manager = Ros2ServiceClientManager(node=mock_node)
        request = SimpleNamespace(scenario_id="SCENARIO_001")

        mock_client = manager._sim_client
        mock_client.wait_for_service.return_value = False

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            manager.call_simulate_scenario(request, timeout_sec=5.0)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_DDS_INIT_FAIL

    def test_service_timeout_raises_sim_recover_eval_failed(
        self, mock_node: MagicMock
    ) -> None:
        """시나리오 5: 응답 타임아웃 초과 시 요청 취소 및 ERR_SIM_RECOVER_EVAL_FAILED 검증"""
        # Given
        manager = Ros2ServiceClientManager(node=mock_node)
        request = SimpleNamespace(scenario_id="SCENARIO_001")

        mock_client = manager._sim_client
        mock_client.wait_for_service.return_value = True

        # 콜백을 실행하지 않아 event.wait()가 타임아웃에 도달하도록 설정
        mock_future = MagicMock()
        mock_client.call_async.return_value = mock_future

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            manager.call_simulate_scenario(request, timeout_sec=0.01)

        mock_future.cancel.assert_called_once()
        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED

    def test_service_future_exception_raises_sim_recover_eval_failed(
        self, mock_node: MagicMock
    ) -> None:
        """시나리오 6: 서비스 내부 런타임 에러(future.exception) 발생 시 예외 변환 검증"""
        # Given
        manager = Ros2ServiceClientManager(node=mock_node)
        request = SimpleNamespace(scenario_id="SCENARIO_001")

        mock_client = manager._sim_client
        mock_client.wait_for_service.return_value = True
        self._setup_mock_future(
            mock_client, exception=RuntimeError("Internal ROS 2 Service Node Error")
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            manager.call_simulate_scenario(request, timeout_sec=1.0)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED
        assert "Internal ROS 2 Service Node Error" in exc_info.value.message
