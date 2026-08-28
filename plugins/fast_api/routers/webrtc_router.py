# File: plugins/fast_api/routers/webrtc_router.py
import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from shared.context.user_context import UserContext
from shared.dtos.global_response_dto import GlobalResponseDto

from plugins.fast_api.adapters.ros2_webrtc_client import Ros2WebRtcSignalingClient
from plugins.fast_api.dependencies.auth import get_current_user_context
from plugins.fast_api.dependencies.clients import get_ros2_webrtc_signaling_client
from plugins.fast_api.schemas.enums import ApiTag
from plugins.fast_api.schemas.requests import (
    WebRtcIceCandidateRequestSchema,
    WebRtcSdpOfferRequestSchema,
)
from plugins.fast_api.schemas.responses import WebRtcSdpAnswerResponseSchema

# Annotated Dependency Type Aliases
CurrentUserContext = Annotated[UserContext, Depends(get_current_user_context)]
WebRtcClient = Annotated[
    Ros2WebRtcSignalingClient, Depends(get_ros2_webrtc_signaling_client)
]

router = APIRouter(prefix="/webrtc", tags=[ApiTag.WEBRTC_SIGNALING.value])


@router.post(
    "/offer",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="WebRTC SDP Offer 전달 및 Answer 획득",
)
async def handle_sdp_offer(
    schema: WebRtcSdpOfferRequestSchema,
    ctx: CurrentUserContext,
    webrtc_client: WebRtcClient,
) -> GlobalResponseDto[WebRtcSdpAnswerResponseSchema]:
    """클라이언트 SDP Offer를 전달하여 C++ 게이트웨이의 SDP Answer를 수신합니다."""
    is_success, sdp_answer = await asyncio.to_thread(
        webrtc_client.call_handle_sdp_offer,
        peer_id=schema.peer_id,
        sdp_offer=schema.sdp_offer,
    )
    response_data = WebRtcSdpAnswerResponseSchema(
        peer_id=schema.peer_id,
        sdp_answer=sdp_answer,
    )
    return GlobalResponseDto.success_response(
        data=response_data, message="SDP Answer generated successfully."
    )


@router.post(
    "/ice-candidate",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="WebRTC ICE Candidate 정보 등록",
)
async def handle_ice_candidate(
    schema: WebRtcIceCandidateRequestSchema,
    ctx: CurrentUserContext,
    webrtc_client: WebRtcClient,
) -> GlobalResponseDto[bool]:
    """ICE Candidate 정보를 WebRTC 게이트웨이로 전달합니다."""
    result = await asyncio.to_thread(
        webrtc_client.call_handle_ice_candidate,
        peer_id=schema.peer_id,
        candidate_json=schema.candidate_json,
    )
    return GlobalResponseDto.success_response(
        data=result, message="ICE candidate registered successfully."
    )


@router.post(
    "/sessions/{peer_id}/close",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="WebRTC 피어 스트리밍 세션 종료",
)
async def close_session(
    peer_id: Annotated[str, Path(..., min_length=1, description="종료할 피어 식별자")],
    ctx: CurrentUserContext,
    webrtc_client: WebRtcClient,
) -> GlobalResponseDto[bool]:
    """WebRTC 피어 세션 리소스를 해제합니다."""
    result = await asyncio.to_thread(
        webrtc_client.call_close_session,
        peer_id=peer_id,
    )
    return GlobalResponseDto.success_response(
        data=result, message="WebRTC session closed successfully."
    )
