# File: plugins/fast_api/dependencies/clients.py
from plugins.fast_api.adapters.ros2_edge_client import Ros2EdgeServiceClient
from plugins.fast_api.adapters.ros2_webrtc_client import Ros2WebRtcSignalingClient


def get_ros2_edge_service_client() -> Ros2EdgeServiceClient:
    """Ros2EdgeServiceClient 인스턴스 주입 팩토리"""
    raise NotImplementedError("Client instance will be wired at composition root.")


def get_ros2_webrtc_signaling_client() -> Ros2WebRtcSignalingClient:
    """Ros2WebRtcSignalingClient 인스턴스 주입 팩토리"""
    raise NotImplementedError("Client instance will be wired at composition root.")
