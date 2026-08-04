# src/shared/dtos/telemetry_packet_dto.py
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TelemetryPacketDto:
    device_id: str
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())
    joint_positions: list[float] = field(default_factory=list)
    joint_torques: list[float] = field(default_factory=list)
    packml_state: str = "EXECUTE"
    is_warning: bool = False
    detected_objects: list[dict[str, Any]] | None = None
    anomaly_score: float | None = 0.0
