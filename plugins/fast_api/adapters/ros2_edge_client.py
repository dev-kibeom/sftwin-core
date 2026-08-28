from typing import Any

from rclpy.node import Node
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode


class Ros2EdgeServiceClient:
    """C++ 에지 제어 노드와의 안전 제어 서비스 통신을 전담하는 클라이언트 어댑터"""

    def __init__(self, node: Node, timeout_sec: float = 5.0) -> None:
        self._node = node
        self._timeout_sec = timeout_sec

        # Service Types: ROS 2 환경에 인터페이스 패키지가 설치되어 있으면 import, 없으면 Any/Dynamic 모의
        try:
            from ros2_ws.src.interfaces.shared_interfaces.srv import (
                GetTelemetryStatus,
                ResetEstopInterlock,
                ResumeRecovery,
                TriggerManualEstop,
            )

            self._estop_srv_type = TriggerManualEstop
            self._reset_srv_type = ResetEstopInterlock
            self._resume_srv_type = ResumeRecovery
            self._telemetry_srv_type = GetTelemetryStatus
        except ImportError:
            self._estop_srv_type = Any
            self._reset_srv_type = Any
            self._resume_srv_type = Any
            self._telemetry_srv_type = Any

        self._estop_client = self._node.create_client(
            self._estop_srv_type, "/sftwin/edge/trigger_manual_estop"
        )
        self._reset_client = self._node.create_client(
            self._reset_srv_type, "/sftwin/edge/reset_interlock"
        )
        self._resume_client = self._node.create_client(
            self._resume_srv_type, "/sftwin/edge/resume_recovery"
        )
        self._telemetry_client = self._node.create_client(
            self._telemetry_srv_type, "/sftwin/edge/get_telemetry"
        )

    def call_trigger_estop(self, reason: str, device_id: str) -> bool:
        """긴급 수동 E-Stop 트리거 서비스 호출"""
        req = getattr(self._estop_srv_type, "Request", lambda: type("Req", (), {})())()
        req.reason = reason
        req.device_id = device_id

        try:
            future = self._estop_client.call_async(req)
            response = future.result()
        except Exception as exc:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT,
                message=f"E-Stop service call timed out or failed: {str(exc)}",
                status_code=504,
            ) from exc

        if not response or not response.is_success:
            err_msg = getattr(response, "error_message", "Failsafe trigger failed")
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_EDGE_FAILSAFE_TRIGGERED,
                message=f"Hardware relay cut or failsafe estop failed: {err_msg}",
                status_code=503,
            )

        return True

    def call_reset_interlock(
        self,
        is_field_inspected: bool,
        is_manager_approved: bool,
        device_id: str,
    ) -> bool:
        """2단계 안전 승인 기반 인터록 리셋 서비스 호출"""
        req = getattr(self._reset_srv_type, "Request", lambda: type("Req", (), {})())()
        req.is_field_inspected = is_field_inspected
        req.is_manager_approved = is_manager_approved
        req.device_id = device_id

        try:
            future = self._reset_client.call_async(req)
            response = future.result()
        except Exception as exc:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT,
                message=f"Reset interlock service call timed out or failed: {str(exc)}",
                status_code=504,
            ) from exc

        if not response or not response.is_success:
            err_msg = getattr(response, "error_message", "Interlock reset denied")
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_EDGE_INTERLOCK_RESET_DENIED,
                message=f"2-step interlock reset denied: {err_msg}",
                status_code=409,
            )

        return True

    def call_resume_recovery(
        self,
        sequence_script: str,
        device_id: str,
    ) -> dict[str, Any]:
        """E-Stop 해제 후 복구 시퀀스 재개 서비스 호출"""
        req = getattr(self._resume_srv_type, "Request", lambda: type("Req", (), {})())()
        req.sequence_script = sequence_script
        req.device_id = device_id

        try:
            future = self._resume_client.call_async(req)
            response = future.result()
        except Exception as exc:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT,
                message=f"Resume recovery service call timed out or failed: {str(exc)}",
                status_code=504,
            ) from exc

        if not response or not response.is_success:
            err_msg = getattr(response, "error_message", "Recovery execution failed")
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED,
                message=f"Recovery script evaluation failed: {err_msg}",
                status_code=422,
            )

        return {
            "is_success": response.is_success,
            "error_message": getattr(response, "error_message", ""),
            "error_code": getattr(response, "error_code", ""),
        }

    def call_get_telemetry(self, device_id: str) -> dict[str, Any]:
        """실시간 에지 텔레메트리 조회 서비스 호출"""
        req = getattr(
            self._telemetry_srv_type, "Request", lambda: type("Req", (), {})()
        )()
        req.device_id = device_id

        try:
            future = self._telemetry_client.call_async(req)
            response = future.result()
        except Exception as exc:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT,
                message=f"Get telemetry service call timed out or failed: {str(exc)}",
                status_code=504,
            ) from exc

        if not response or not response.is_success:
            err_msg = getattr(response, "error_message", "Telemetry stream unavailable")
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT,
                message=f"Failed to fetch telemetry status: {err_msg}",
                status_code=502,
            )

        return {
            "device_id": response.device_id,
            "timestamp_ns": getattr(response, "timestamp_ns", 0),
            "joint_positions": list(getattr(response, "joint_positions", [])),
            "joint_torques": list(getattr(response, "joint_torques", [])),
            "anomaly_score": getattr(response, "anomaly_score", 0.0),
            "is_warning": getattr(response, "is_warning", False),
        }
