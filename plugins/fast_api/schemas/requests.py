# File: plugins/fast_api/schemas/requests.py
from typing import Any

from pydantic import BaseModel, Field

from plugins.fast_api.schemas.enums import SignalingMessageType


# --- Asset & Twin Schemas ---
class RegisterAssetRequestSchema(BaseModel):
    asset_name: str = Field(..., min_length=1, description="자산 명칭")
    asset_type: str = Field(
        ..., min_length=1, description="AAS 자산 분류 (ROBOT, AMR, CNC 등)"
    )
    cad_file_path: str | None = Field(None, description="CAD/3D 모델 파일 경로")
    kinematics_metadata: dict[str, Any] = Field(
        default_factory=dict, description="기구학 제원 (DoF, DH 파라미터)"
    )
    submodels: dict[str, Any] = Field(
        default_factory=dict, description="AAS 서브모델 메타데이터"
    )


class AssetPlacementItemSchema(BaseModel):
    asset_id: str = Field(..., min_length=1)
    target_pos_x: float | None = Field(None, description="드래그 앤 드롭 X좌표 (m)")
    target_pos_y: float | None = Field(None, description="드래그 앤 드롭 Y좌표 (m)")
    target_pos_z: float | None = Field(None, description="드래그 앤 드롭 Z좌표 (m)")


class ReconstructTwinRequestSchema(BaseModel):
    baseline_name: str = Field(..., min_length=1, description="베이스라인 명칭")
    source_log_path: str = Field(
        ..., min_length=1, description="원천 센서 로그 파일 경로"
    )


class CalibrateDynamicsRequestSchema(BaseModel):
    baseline_id: str = Field(..., min_length=1, description="대상 베이스라인 ID")
    source_log_path: str = Field(
        ..., min_length=1, description="캘리브레이션용 센서 로그 경로"
    )
    target_tolerance_percent: float = Field(
        default=5.0, gt=0.0, le=5.0, description="목표 오차 허용 범위(%)"
    )
    max_iterations: int = Field(
        default=10, ge=1, le=100, description="최대 반복 피팅 횟수"
    )
    initial_parameters: dict[str, Any] = Field(
        default_factory=dict, description="초기 튜닝 파라미터 (감쇠/마찰 등)"
    )


class CanvasBoundsSchema(BaseModel):
    max_x: float = Field(default=50.0, gt=0.0)
    max_y: float = Field(default=50.0, gt=0.0)
    max_z: float = Field(default=10.0, gt=0.0)


class OptimizeLayoutRequestSchema(BaseModel):
    assets: list[AssetPlacementItemSchema] = Field(..., min_length=1)
    canvas_bounds: CanvasBoundsSchema = Field(default_factory=CanvasBoundsSchema)


# --- Simulation Schemas ---
class TrajectoryPointSchema(BaseModel):
    asset_id: str = Field(..., min_length=1, description="설비/로봇 식별자")
    position_x: float = Field(..., description="X 좌표 (m)")
    position_y: float = Field(..., description="Y 좌표 (m)")
    position_z: float = Field(..., description="Z 좌표 (m)")
    velocity: float = Field(default=0.0, ge=0.0, description="이동 속도 (m/s)")
    time_sec: float = Field(default=0.0, ge=0.0, description="도달 목표 시간 (초)")


class RunFmsSimulationRequestSchema(BaseModel):
    scenario_id: str = Field(..., min_length=1, description="시뮬레이션 시나리오 ID")
    baseline_id: str = Field(..., min_length=1, description="기반 트윈 베이스라인 ID")
    assets: list[RegisterAssetRequestSchema] = Field(
        default_factory=list, description="시뮬레이션 대상 자산 목록"
    )
    task_waypoints: list[TrajectoryPointSchema] = Field(
        default_factory=list, description="검증할 공정/로봇 이동 웨이포인트 목록"
    )
    max_duration_sec: float = Field(
        default=30.0, ge=1.0, le=120.0, description="최대 시뮬레이션 제한 시간 (초)"
    )


class InjectFaultRequestSchema(BaseModel):
    fault_type: str = Field(
        ...,
        description="결함 유형 (CONVEYOR_JAM, ROBOT_MOTOR_OVERHEAT, AMR_PATH_BLOCKED)",
    )
    target: str = Field(..., min_length=1, description="결함 주입 대상 설비 식별자")
    trigger_time_sec: float = Field(
        default=5.0, ge=0.0, description="결함 발동 시점 (초)"
    )
    obstacle_distance_m: float = Field(
        default=999.0, description="장애물 감지 거리 (AMR 결함용)"
    )


# --- Deployment ---
class Vda5050ConfigSchema(BaseModel):
    mqtt_broker_url: str = Field(
        default="mqtt://localhost:1883", description="MQTT 브로커 주소"
    )
    topic_prefix: str = Field(default="uagv/v2", description="VDA 5050 토픽 접두사")
    manufacturer: str = Field(default="SFTWIN_ROBOTICS", description="AGV/AMR 제조사명")
    serial_number: str = Field(default="AGV-001", description="대상 기기 일련번호")


class DeploySim2RealRequestSchema(BaseModel):
    package_id: str = Field(
        ..., min_length=1, description="배포 패키지 고유 ID (또는 deployment_id)"
    )
    format_type: str = Field(
        default="VDA5050",
        description="배포 포맷 (VDA5050 | ROS2_WS | CONTAINER)",
    )
    ros2_ws_path: str | None = Field(
        default=None,
        description="ROS 2 워크스페이스 대상 경로 (format_type이 ROS2_WS인 경우)",
    )
    config: Vda5050ConfigSchema = Field(
        default_factory=Vda5050ConfigSchema,
        description="VDA 5050 MQTT 연동 설정",
    )


# --- Procurement & Orders ---
class GenerateQuoteRequestSchema(BaseModel):
    asset_ids: list[str] = Field(
        ..., min_length=1, description="견적 대상 설비 ID 목록"
    )


class ProcessProductionOrderRequestSchema(BaseModel):
    product_code: str = Field(..., min_length=1)
    target_quantity: int = Field(..., gt=0)
    factory_phase: str = Field(..., description="BASELINE | FMS_OPTIMIZED")
    order_id: str | None = None


# --- Edge Control & Safety Schemas ---
class TriggerManualEstopRequestSchema(BaseModel):
    reason: str = Field(..., min_length=1, description="비상 정지 사유")
    device_id: str = Field(default="EDGE_NODE_001", description="대상 디바이스 ID")


class ResetInterlockRequestSchema(BaseModel):
    is_field_inspected: bool = Field(..., description="현장 1차 안전 점검 완료 여부")
    is_manager_approved: bool = Field(..., description="관리자 2차 리셋 승인 여부")
    device_id: str = Field(default="EDGE_NODE_001", description="대상 디바이스 ID")


class ResumeRecoveryRequestSchema(BaseModel):
    sequence_script: str = Field(
        ...,
        min_length=1,
        description="복구 실행 시퀀스 스크립트 또는 시나리오 식별자",
    )
    device_id: str = Field(default="EDGE_NODE_001", description="대상 디바이스 ID")


# --- WebRTC Signaling Schema ---
class SignalingMessageSchema(BaseModel):
    type: SignalingMessageType
    peer_id: str = Field(..., min_length=1)
    sdp: str | None = None
    candidate: str | None = None


# --- KPI Report Schemas ---
class GenerateDualKpiReportRequestSchema(BaseModel):
    baseline_oee: float = Field(
        ..., ge=0.0, le=100.0, description="기준 시나리오 OEE (%)"
    )
    improved_oee: float = Field(
        ..., ge=0.0, le=100.0, description="개선 시나리오 OEE (%)"
    )
    baseline_fpy: float = Field(
        ..., ge=0.0, le=100.0, description="기준 시나리오 FPY (%)"
    )
    improved_fpy: float = Field(
        ..., ge=0.0, le=100.0, description="개선 시나리오 FPY (%)"
    )
    turnkey_quote_cost: float = Field(
        ..., ge=0.0, description="B2B 턴키 도입 견적 비용 (KRW)"
    )
