# File: plugins/fast_api/routers/edge_router.py
import asyncio
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from shared.context.user_context import UserContext
from shared.dtos.global_response_dto import GlobalResponseDto

from plugins.fast_api.adapters.ros2_edge_client import Ros2EdgeServiceClient
from plugins.fast_api.dependencies.auth import get_current_user_context
from plugins.fast_api.dependencies.clients import get_ros2_edge_service_client
from plugins.fast_api.schemas.enums import ApiTag
from plugins.fast_api.schemas.requests import (
    ResetInterlockRequestSchema,
    ResumeRecoveryRequestSchema,
    TriggerManualEstopRequestSchema,
)

# Annotated Dependency Type Aliases
CurrentUserContext = Annotated[UserContext, Depends(get_current_user_context)]
EdgeServiceClient = Annotated[
    Ros2EdgeServiceClient, Depends(get_ros2_edge_service_client)
]

router = APIRouter(prefix="/edge", tags=[ApiTag.EDGE_CONTROL.value])


@router.post(
    "/estop",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="긴급 하드웨어 E-Stop 트리거",
)
async def trigger_manual_estop(
    schema: TriggerManualEstopRequestSchema,
    ctx: CurrentUserContext,
    edge_client: EdgeServiceClient,
) -> GlobalResponseDto[bool]:
    """긴급 E-Stop 호출을 ROS 2 에지 서비스 클라이언트로 비동기 위임합니다."""
    result = await asyncio.to_thread(
        edge_client.call_trigger_estop,
        reason=schema.reason,
        device_id=schema.device_id,
    )
    return GlobalResponseDto.success_response(
        data=result, message="E-Stop triggered successfully."
    )


@router.post(
    "/reset-interlock",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="2단계 안전 승인 기반 인터록 리셋",
)
async def reset_interlock(
    schema: ResetInterlockRequestSchema,
    ctx: CurrentUserContext,
    edge_client: EdgeServiceClient,
) -> GlobalResponseDto[bool]:
    """현장 점검 및 관리자 2단계 승인 플래그를 ROS 2 에지 서비스로 전달합니다."""
    result = await asyncio.to_thread(
        edge_client.call_reset_interlock,
        is_field_inspected=schema.is_field_inspected,
        is_manager_approved=schema.is_manager_approved,
        device_id=schema.device_id,
    )
    return GlobalResponseDto.success_response(
        data=result, message="Safety interlock reset successfully."
    )


@router.post(
    "/resume-recovery",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="E-Stop 해제 후 복구 시퀀스 재개",
)
async def resume_recovery(
    schema: ResumeRecoveryRequestSchema,
    ctx: CurrentUserContext,
    edge_client: EdgeServiceClient,
) -> GlobalResponseDto[dict[str, Any]]:
    """복구 시퀀스 스크립트 실행을 에지 서비스로 위임합니다."""
    result = await asyncio.to_thread(
        edge_client.call_resume_recovery,
        sequence_script=schema.sequence_script,
        device_id=schema.device_id,
    )
    return GlobalResponseDto.success_response(
        data=result, message="Recovery execution initiated successfully."
    )


@router.get(
    "/telemetry/{device_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="실시간 에지 디바이스 관측 텔레메트리 조회",
)
async def get_telemetry(
    device_id: str,
    ctx: CurrentUserContext,
    edge_client: EdgeServiceClient,
) -> GlobalResponseDto[dict[str, Any]]:
    """에지 디바이스 텔레메트리 조회를 서비스 클라이언트로 위임합니다."""
    telemetry_data = await asyncio.to_thread(
        edge_client.call_get_telemetry,
        device_id=device_id,
    )
    return GlobalResponseDto.success_response(
        data=telemetry_data, message="Telemetry retrieved successfully."
    )
