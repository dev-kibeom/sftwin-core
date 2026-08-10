from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from src.kpi_b2b.b2b_procurement.application.generate_quote.b2b_quote_dto import (
    B2bQuoteDto,
)
from src.kpi_b2b.b2b_procurement.application.layout_mirroring.session_data_dto import (
    SessionDataDto,
)
from src.kpi_b2b.dependencies import get_current_user, get_procurement_facade
from src.kpi_b2b.facades.procurement_command_facade import ProcurementCommandFacade
from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.security.user_context import UserContext

router = APIRouter(prefix="/api/v1/procurement", tags=["B2B Procurement"])


class QuoteRequest(BaseModel):
    asset_ids: list[str]


class SessionRequest(BaseModel):
    baseline_id: str


@router.post("/quotes", response_model=GlobalResponseDto[B2bQuoteDto])
async def generate_turnkey_quote(
    request: QuoteRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    ctx: UserContext = Depends(get_current_user),
    facade: ProcurementCommandFacade = Depends(get_procurement_facade),
):
    """채택된 설비 목록(asset_ids)을 기반으로 B2B 마켓플레이스 턴키 견적을 요청합니다 (멱등성 보장)."""
    result_dto = facade.generate_quote(
        asset_ids=request.asset_ids, idempotency_key=idempotency_key, ctx=ctx
    )
    return GlobalResponseDto.success_response(data=result_dto)


@router.post("/expert-sessions", response_model=GlobalResponseDto[SessionDataDto])
async def create_expert_session(
    request: SessionRequest,
    ctx: UserContext = Depends(get_current_user),
    facade: ProcurementCommandFacade = Depends(get_procurement_facade),
):
    """3D 미러링 데이터 스트리밍을 위한 비대면 전문가 상담 1회성 세션을 발급합니다."""
    result_dto = facade.create_expert_session(baseline_id=request.baseline_id, ctx=ctx)
    return GlobalResponseDto.success_response(data=result_dto)
