# plugins/fast_api/schemas/responses.py
from pydantic import BaseModel, Field


class WebRtcSdpAnswerResponseSchema(BaseModel):
    peer_id: str = Field(..., min_length=1, description="피어 식별자")
    sdp_answer: str = Field(..., description="생성된 SDP Answer 문자열")
