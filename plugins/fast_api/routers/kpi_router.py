"""
===============================================================================
[File Name] kpi_router.py
[Location ] /plugins/fast_api/routers/kpi_router.py
[Description]
 - KPI Dashboard 컴포넌트의 최외곽 Inbound Router Adapter (Driving Adapter)입니다.
 - 실시간 제조 KPI(OEE/FPY) 연산 및 FMS 도입 전/후 듀얼 KPI 비교 & ROI 산출 기능을 제공합니다.
===============================================================================
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from kpi_b2b.facades.kpi_query_facade import KpiQueryFacade
from kpi_b2b.kpi_dashboard.application.calculate_kpi.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from kpi_b2b.contracts.dtos.kpi_report_dto import (
    KpiReportDto,
)
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_usecase import (
    DualKpiReportDto,
    GenerateDualKpiReportUseCase,
)
from pydantic import BaseModel, Field
from shared.dtos.global_response_dto import GlobalResponseDto
from shared.context.user_context import UserContext, get_current_user

from plugins.fast_api.dependencies import (
    get_calculate_kpi_usecase,
    get_generate_dual_kpi_report_usecase,
    get_kpi_facade,
)

router = APIRouter(prefix="/api/v1/kpi", tags=["KPI Dashboard"])


# ==========================================
# Request DTO Schemas
# ==========================================
class DualKpiReportRequestDto(BaseModel):
    baseline_oee: float = Field(
        ..., description="FMS 도입 전 베이스라인 OEE (0.0 ~ 1.0)"
    )
    improved_oee: float = Field(..., description="FMS 도입 후 개선된 OEE (0.0 ~ 1.0)")
    baseline_fpy: float = Field(
        ..., description="FMS 도입 전 베이스라인 직행수율 FPY (0.0 ~ 1.0)"
    )
    improved_fpy: float = Field(
        ..., description="FMS 도입 후 개선된 직행수율 FPY (0.0 ~ 1.0)"
    )
    turnkey_quote_cost: float = Field(
        ..., description="B2B 마켓플레이스 턴키 견적가 (원)"
    )


# ==========================================
# Endpoints
# ==========================================
@router.get(
    "/oee/{sim_id}",
    response_model=GlobalResponseDto[KpiReportDto],
    status_code=status.HTTP_200_OK,
    summary="[파사드 조회] 시뮬레이션 OEE/KPI 조회",
    description="지정된 시뮬레이션 ID의 OEE, TEEP, FPY 등 제조 KPI를 KpiQueryFacade를 통해 조회합니다.",
)
async def get_simulation_oee(
    sim_id: str,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    facade: Annotated[KpiQueryFacade, Depends(get_kpi_facade)],
) -> GlobalResponseDto[KpiReportDto]:
    """시뮬레이션 OEE 산출 (파사드 처리)"""
    result_dto = facade.calculate_oee(sim_id=sim_id, ctx=ctx)
    return GlobalResponseDto.success_response(data=result_dto)


@router.get(
    "/calculate/{sim_id}",
    response_model=GlobalResponseDto[KpiReportDto],
    status_code=status.HTTP_200_OK,
    summary="[Step 3] 실시간 제조 KPI (OEE, TEEP, FPY) 산출",
    description="시뮬레이션 가동 결과 시계열 로그를 기반으로 ISA-95 표준 종합설비효율(OEE), TEEP 및 FPY 수치를 연산합니다.",
)
async def calculate_kpi(
    sim_id: str,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[CalculateKpiUseCase, Depends(get_calculate_kpi_usecase)],
) -> GlobalResponseDto[KpiReportDto]:
    """단일 시뮬레이션 KPI 산출 (유스케이스 직접 처리)"""
    result = use_case.execute(sim_id=sim_id, company_id=ctx.company_id)
    return GlobalResponseDto.success_response(
        data=result,
        message="KPI report calculated successfully.",
    )


@router.post(
    "/dual-report",
    response_model=GlobalResponseDto[DualKpiReportDto],
    status_code=status.HTTP_200_OK,
    summary="[Step 3/5] FMS 도입 전/후 듀얼 KPI 비교 및 ROI 회수 기간 산출",
    description="FMS 도입 전/후의 OEE 및 FPY 개선율을 실시간 비교하고 B2B 견적가 대비 정량적 투자 회수 기간(ROI 개월 수)을 산출합니다.",
)
async def generate_dual_kpi_report(
    payload: DualKpiReportRequestDto,
    ctx: Annotated[UserContext, Depends(get_current_user)],
    use_case: Annotated[
        GenerateDualKpiReportUseCase, Depends(get_generate_dual_kpi_report_usecase)
    ],
) -> GlobalResponseDto[DualKpiReportDto]:
    """듀얼 KPI 비교 및 ROI 산출 (유스케이스 직접 처리)"""
    result = use_case.execute(
        baseline_oee=payload.baseline_oee,
        improved_oee=payload.improved_oee,
        baseline_fpy=payload.baseline_fpy,
        improved_fpy=payload.improved_fpy,
        turnkey_quote_cost=payload.turnkey_quote_cost,
    )
    return GlobalResponseDto.success_response(
        data=result,
        message="Dual KPI and ROI comparison report generated successfully.",
    )
