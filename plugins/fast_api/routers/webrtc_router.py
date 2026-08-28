# File: plugins/fast_api/routers/webrtc_router.py
import asyncio
import json
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Path,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import ValidationError
from shared.context.user_context import UserContext
from shared.dtos.global_response_dto import GlobalResponseDto

from plugins.fast_api.adapters.ros2_webrtc_client import Ros2WebRtcSignalingClient
from plugins.fast_api.dependencies.auth import get_current_user_context
from plugins.fast_api.dependencies.clients import get_ros2_webrtc_signaling_client
from plugins.fast_api.schemas.enums import ApiTag, SignalingMessageType
from plugins.fast_api.schemas.requests import (
    SignalingMessageSchema,
    WebRtcIceCandidateRequestSchema,
    WebRtcSdpOfferRequestSchema,
)
from plugins.fast_api.schemas.responses import WebRtcSdpAnswerResponseSchema

CurrentUserContext = Annotated[UserContext, Depends(get_current_user_context)]
WebRtcClient = Annotated[
    Ros2WebRtcSignalingClient, Depends(get_ros2_webrtc_signaling_client)
]

router = APIRouter(prefix="/webrtc", tags=[ApiTag.WEBRTC_SIGNALING.value])


# --- WebRTC WebSocket Signaling Channel ---
@router.websocket("/signaling")
async def webrtc_websocket_signaling(
    websocket: WebSocket,
    webrtc_client: WebRtcClient,
) -> None:
    """Three.js 클라이언트와 SDP Offer/Answer 및 ICE Candidate를 교환하는 양방향 WebSocket 엔드포인트"""
    await websocket.accept()
    active_peer_id: str | None = None

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
                msg = SignalingMessageSchema(**data)
            except (json.JSONDecodeError, ValidationError) as err:
                await websocket.send_json(
                    {"error": "Invalid signaling message format", "details": str(err)}
                )
                continue

            active_peer_id = msg.peer_id

            if msg.type == SignalingMessageType.OFFER:
                if not msg.sdp:
                    await websocket.send_json(
                        {"error": "SDP payload missing for OFFER"}
                    )
                    continue

                is_success, sdp_answer = await asyncio.to_thread(
                    webrtc_client.call_handle_sdp_offer,
                    peer_id=msg.peer_id,
                    sdp_offer=msg.sdp,
                )
                if is_success:
                    await websocket.send_json(
                        {
                            "type": SignalingMessageType.ANSWER.value,
                            "peer_id": msg.peer_id,
                            "sdp": sdp_answer,
                        }
                    )
                else:
                    await websocket.send_json({"error": "Failed to handle SDP Offer"})

            elif msg.type == SignalingMessageType.CANDIDATE:
                if not msg.candidate:
                    continue
                await asyncio.to_thread(
                    webrtc_client.call_handle_ice_candidate,
                    peer_id=msg.peer_id,
                    candidate_json=msg.candidate,
                )

            elif msg.type == SignalingMessageType.PING:
                await websocket.send_json({"type": SignalingMessageType.PONG.value})

    except WebSocketDisconnect:
        if active_peer_id:
            await asyncio.to_thread(webrtc_client.call_close_session, active_peer_id)


# --- REST API Endpoints ---
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
    result = await asyncio.to_thread(
        webrtc_client.call_close_session,
        peer_id=peer_id,
    )
    return GlobalResponseDto.success_response(
        data=result, message="WebRTC session closed successfully."
    )
