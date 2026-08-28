# File: plugins/fast_api/adapters/ros2_webrtc_client.py
import threading
from typing import Any

from rclpy.node import Node
from rclpy.task import Future
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode


class Ros2WebRtcSignalingClient:
    """C++ WebRTC 게이트웨이 노드와의 시그널링 교환 서비스 통신을 전담하는 클라이언트 어댑터"""

    def __init__(self, node: Node, timeout_sec: float = 5.0) -> None:
        self._node = node
        self._timeout_sec = timeout_sec

        try:
            from ros2_ws.src.interfaces.shared_interfaces.srv import (
                ClosePeerSession,
                GetWebRtcSession,
                HandleIceCandidate,
                HandleSdpOffer,
            )

            self._sdp_srv_type = HandleSdpOffer
            self._ice_srv_type = HandleIceCandidate
            self._close_srv_type = ClosePeerSession
            self._session_srv_type = GetWebRtcSession
        except ImportError:
            self._sdp_srv_type = Any
            self._ice_srv_type = Any
            self._close_srv_type = Any
            self._session_srv_type = Any

        self._sdp_client = self._node.create_client(
            self._sdp_srv_type, "/sftwin/webrtc/handle_sdp_offer"
        )
        self._ice_client = self._node.create_client(
            self._ice_srv_type, "/sftwin/webrtc/handle_ice_candidate"
        )
        self._close_client = self._node.create_client(
            self._close_srv_type, "/sftwin/webrtc/close_peer_session"
        )
        self._session_client = self._node.create_client(
            self._session_srv_type, "/sftwin/webrtc/get_session"
        )

    def _wait_for_future(self, future: Future, service_name: str) -> Any:
        """ROS 2 Future 응답을 스레드 안전하게 타임아웃 대기"""
        event = threading.Event()
        future.add_done_callback(lambda _: event.set())

        if not event.wait(timeout=self._timeout_sec):
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT,
                message=f"ROS 2 WebRTC service call to [{service_name}] timed out after {self._timeout_sec}s",
                status_code=504,
            )

        exc = future.exception()
        if exc is not None:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT,
                message=f"ROS 2 WebRTC service call to [{service_name}] failed: {str(exc)}",
                status_code=504,
            ) from exc

        return future.result()

    def call_handle_sdp_offer(self, peer_id: str, sdp_offer: str) -> tuple[bool, str]:
        """SDP Offer 전달 및 SDP Answer 획득"""
        req = getattr(self._sdp_srv_type, "Request", lambda: type("Req", (), {})())()
        req.peer_id = peer_id
        req.sdp_offer = sdp_offer

        future = self._sdp_client.call_async(req)
        response = self._wait_for_future(future, "/sftwin/webrtc/handle_sdp_offer")

        if not response or not getattr(response, "is_success", False):
            return False, ""

        return True, getattr(response, "sdp_answer", "")

    def call_handle_ice_candidate(self, peer_id: str, candidate_json: str) -> bool:
        """ICE Candidate 전달 및 등록"""
        req = getattr(self._ice_srv_type, "Request", lambda: type("Req", (), {})())()
        req.peer_id = peer_id
        req.candidate_json = candidate_json

        future = self._ice_client.call_async(req)
        response = self._wait_for_future(future, "/sftwin/webrtc/handle_ice_candidate")

        return bool(response and getattr(response, "is_success", False))

    def call_close_session(self, peer_id: str) -> bool:
        """WebRTC 피어 세션 정상 종료"""
        req = getattr(self._close_srv_type, "Request", lambda: type("Req", (), {})())()
        req.peer_id = peer_id

        future = self._close_client.call_async(req)
        response = self._wait_for_future(future, "/sftwin/webrtc/close_peer_session")

        return bool(response and getattr(response, "is_success", False))
