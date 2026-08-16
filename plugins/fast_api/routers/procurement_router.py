"""
===============================================================================
[File Name] procurement_router.py
[Location ] /plugins/fast_api/routers/procurement_router.py
[Description]
 - B2B Procurement 컴포넌트의 최외곽 Inbound Router Adapter (Driving Adapter)입니다.
===============================================================================
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from kpi_b2b.b2b_procurement.application.generate_quote.b2b_quote_dto import (
    B2bQuoteDto,
)
from kpi_b2b.b2b_procurement.application.layout_mirroring.session_data_dto import (
    SessionDataDto,
)
from kpi_b2b.b2b_procurement.application.process_production_order.process_production_order_usecase import (
    ProcessProductionOrderUseCase,
)
from kpi_b2b.b2b_procurement.application.process_production_order.production_order_dto import (
    ProductionOrderRequestDto,
    ProductionOrderResultDto,
)
from kpi_b2b.facades.procurement_command_facade import ProcurementCommandFacade
from pydantic import BaseModel, Field
from shared.dtos.global_response_dto import GlobalResponseDto
from shared.context.user_context import UserContext, get_current_user

from plugins.fast_api.dependencies import (
    get_process_production_order_usecase,
    get_procurement_facade,
)

router = APIRouter(prefix="/api/v1/procurement", tags=["B2B Procurement"])


class QuoteRequest(BaseModel):
    asset_ids: list[str] = Field(
        ..., description="턴키 견적 산출 대상 AAS 설비 ID 목록"
    )


class SessionRequest(BaseModel):
    baseline_id: str = Field(..., description="디지털 트윈 베이스라인 ID")


@router.post(
    "/quotes",
    response_model=GlobalResponseDto[B2bQuoteDto],
    status_code=status.HTTP_201_CREATED,
    summary="[Step 2/5] B2B 마켓플레이스 턴키 견적 산출",
)
async def generate_turnkey_quote(
    request: QuoteRequest,  # 1. Body
    ctx: Annotated[UserContext, Depends(get_current_user)],  # 2. DI Context
    facade: Annotated[
        ProcurementCommandFacade, Depends(get_procurement_facade)
    ],  # 3. DI Facade
    idempotency_key: str = Header(
        ..., alias="Idempotency-Key"
    ),  # 4. Header Default (맨 뒤로 배치)
) -> GlobalResponseDto[B2bQuoteDto]:
    result_dto = facade.generate_quote(
        asset_ids=request.asset_ids, idempotency_key=idempotency_key, ctx=ctx
    )
    return GlobalResponseDto.success_response(data=result_dto)


@router.post(
    "/expert-sessions",
    response_model=GlobalResponseDto[SessionDataDto],
    status_code=status.HTTP_201_CREATED,
    summary="[Step 2] 비대면 전문가 상담 세션 발급",
)
async def create_expert_session(
    request: SessionRequest,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    facade: Annotated[ProcurementCommandFacade, Depends(get_procurement_facade)],
) -> GlobalResponseDto[SessionDataDto]:
    result_dto = facade.create_expert_session(baseline_id=request.baseline_id, ctx=ctx)
    return GlobalResponseDto.success_response(data=result_dto)


@router.post(
    "/orders",
    response_model=GlobalResponseDto[ProductionOrderResultDto],
    status_code=status.HTTP_200_OK,
    summary="[Step 1/3] 생산 발주 투입 및 PackML 제어 전환",
)
async def process_production_order(
    payload: ProductionOrderRequestDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[
        ProcessProductionOrderUseCase, Depends(get_process_production_order_usecase)
    ],
) -> GlobalResponseDto[ProductionOrderResultDto]:
    result = use_case.execute(request_dto=payload, ctx=ctx)
    return GlobalResponseDto.success_response(
        data=result,
        message="Production order processed and dispatched into EXECUTE state.",
    )
