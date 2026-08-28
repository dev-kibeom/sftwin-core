# File: plugins/fast_api/schemas/enums.py
from enum import Enum


class HttpHeaderKey(str, Enum):
    AUTHORIZATION = "Authorization"
    X_TRACE_ID = "X-Trace-Id"
    X_IDEMPOTENCY_KEY = "X-Idempotency-Key"


class ApiTag(str, Enum):
    ASSET_LIBRARY = "Asset Library"
    DIGITAL_TWIN = "Digital Twin & Layout"
    SIMULATION = "Simulation & Deployment"
    PROCUREMENT_KPI = "B2B Procurement & KPI"
    EDGE_CONTROL = "Edge Control & Monitoring"
    WEBRTC_SIGNALING = "WebRTC Video Signaling"


class SignalingMessageType(str, Enum):
    OFFER = "OFFER"
    ANSWER = "ANSWER"
    CANDIDATE = "CANDIDATE"
    CLOSE = "CLOSE"
    PING = "PING"
    PONG = "PONG"
