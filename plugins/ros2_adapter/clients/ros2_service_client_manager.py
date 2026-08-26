import threading
from types import SimpleNamespace
from typing import Any

from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger


class Ros2ServiceClientManager:
    """ROS 2 비동기 Service Client 풀 관리 및 E-Stop 퍼블리셔 제어 클래스"""

    def __init__(self, node: Any) -> None:
        self._node = node
        self._system_logger = GlobalSystemLogger(
            component_name="Ros2ServiceClientManager"
        )

        # Service Clients 초기화 (모의/실제 ROS 2 메시지 타입 대응)
        self._sim_client = self._node.create_client(
            SimpleNamespace, "/sftwin/simulate_scenario"
        )
        self._amr_bypass_client = self._node.create_client(
            SimpleNamespace, "/sftwin/plan_amr_bypass"
        )
        self._arm_plan_client = self._node.create_client(
            SimpleNamespace, "/sftwin/plan_manipulator_trajectory"
        )
        self._scene_client = self._node.create_client(
            SimpleNamespace, "/sftwin/update_planning_scene"
        )

        # E-Stop Publisher 초기화
        self._estop_publisher = self._node.create_publisher(
            SimpleNamespace, "/failsafe/estop", 10
        )

    def _call_service_sync(
        self,
        client: Any,
        request: Any,
        timeout_sec: float,
        service_name: str,
    ) -> Any:
        """ROS 2 서비스 비동기 요청 후 threading.Event 기반 동기 안전 대기"""
        # 1. 서비스 가용성 점검 (Service Unavailable Guard)
        if not client.wait_for_service(timeout_sec=2.0):
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_EDGE_DDS_INIT_FAIL,
                custom_message=f"ROS 2 service '{service_name}' is not reachable.",
            )

        # 2. 비동기 요청 발행 및 Event 동기화 객체 구성
        event = threading.Event()
        future = client.call_async(request)

        def _on_complete(_: Any) -> None:
            event.set()

        future.add_done_callback(_on_complete)

        # 3. threading.Event를 이용한 안전한 동기 블로킹 대기 (Spin 데드락 방지)
        completed = event.wait(timeout=timeout_sec)
        if not completed:
            if hasattr(future, "cancel"):
                future.cancel()
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED,
                custom_message=f"ROS 2 service '{service_name}' call exceeded timeout of {timeout_sec}s.",
            )

        # 4. 비동기 실행 중 발생한 예외 점검 (future.exception 확인)
        if hasattr(future, "exception"):
            exc = future.exception()
            if exc is not None:
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED,
                    custom_message=f"ROS 2 service '{service_name}' raised an exception: {exc}",
                )

        # 5. 결과 검증 및 반환
        try:
            return future.result()
        except Exception as exc:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED,
                custom_message=f"ROS 2 service '{service_name}' raised an exception: {exc}",
            ) from exc

    def call_simulate_scenario(self, request: Any, timeout_sec: float = 15.0) -> Any:
        """MuJoCo 시뮬레이션 서비스 호출"""
        return self._call_service_sync(
            self._sim_client,
            request,
            timeout_sec=timeout_sec,
            service_name="/sftwin/simulate_scenario",
        )

    def call_plan_amr_bypass(self, request: Any, timeout_sec: float = 5.0) -> Any:
        """Nav2 AMR 바이패스 경로 생성 서비스 호출"""
        return self._call_service_sync(
            self._amr_bypass_client,
            request,
            timeout_sec=timeout_sec,
            service_name="/sftwin/plan_amr_bypass",
        )

    def call_plan_arm_trajectory(self, request: Any, timeout_sec: float = 5.0) -> Any:
        """MoveIt 2 매니퓰레이터 궤적 생성 서비스 호출"""
        return self._call_service_sync(
            self._arm_plan_client,
            request,
            timeout_sec=timeout_sec,
            service_name="/sftwin/plan_manipulator_trajectory",
        )

    def call_update_planning_scene(self, request: Any, timeout_sec: float = 3.0) -> Any:
        """MoveIt 2 동적 3D Planning Scene 갱신 서비스 호출"""
        return self._call_service_sync(
            self._scene_client,
            request,
            timeout_sec=timeout_sec,
            service_name="/sftwin/update_planning_scene",
        )

    def publish_estop(
        self,
        action_type: str = "ESTOP",
        trigger_reason: str = "CORE_FAILSAFE_TRIGGERED",
    ) -> None:
        """E-Stop 비상 정지 토픽 즉시 브로드캐스트"""
        msg = SimpleNamespace(
            action_type=action_type,
            trigger_reason=trigger_reason,
        )
        self._estop_publisher.publish(msg)
        self._system_logger.warn(
            "Failsafe E-Stop broadcasted to /failsafe/estop",
            extra={"action_type": action_type, "trigger_reason": trigger_reason},
        )

    def shutdown(self) -> None:
        """매니저 리소스 정리 및 수명 주기 종료"""
        self._is_running = False
        self._logger.info("Ros2ServiceClientManager shutdown completed")
