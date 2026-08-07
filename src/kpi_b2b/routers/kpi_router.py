from fastapi import APIRouter, Depends

from src.kpi_b2b.dependencies import get_current_user, get_kpi_facade
from src.kpi_b2b.facades.kpi_query_facade import KpiQueryFacade
from src.kpi_b2b.kpi_dashboard.dtos.kpi_report_dto import KpiReportDto
from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.security.user_context import UserContext

router = APIRouter(prefix="/api/v1/kpi", tags=["KPI Dashboard"])


@router.get("/oee/{sim_id}", response_model=GlobalResponseDto[KpiReportDto])
async def get_simulation_oee(
    sim_id: str,
    ctx: UserContext = Depends(get_current_user),
    facade: KpiQueryFacade = Depends(get_kpi_facade),
):
    """지정된 시뮬레이션 ID의 OEE, TEEP, FPY 등 제조 KPI를 산출하여 반환합니다."""
    result_dto = facade.calculate_oee(sim_id=sim_id, ctx=ctx)
    return GlobalResponseDto.success_response(data=result_dto)
