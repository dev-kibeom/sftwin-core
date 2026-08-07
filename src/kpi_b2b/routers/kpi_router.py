"""
@file kpi_router.py
@description KPI OEE 조회 REST API 엔드포인트
"""

from fastapi import APIRouter, Depends

from src.kpi_b2b.facades.kpi_query_facade import KpiQueryFacade
from src.kpi_b2b.kpi_dashboard.dtos.kpi_report_dto import KpiReportDto
from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.security.user_context import UserContext

router = APIRouter(prefix="/api/v1/kpi", tags=["KPI Dashboard"])


# Stub: 실제 환경에서는 security/jwt_auth_interceptor.py 의 get_current_user 주입
def get_current_user() -> UserContext:
    pass


# Stub: 의존성 주입(DI) 컨테이너에서 파사드 인스턴스를 가져오는 함수
def get_kpi_facade() -> KpiQueryFacade:
    pass


@router.get("/oee/{sim_id}", response_model=GlobalResponseDto[KpiReportDto])
async def get_simulation_oee(
    sim_id: str,
    ctx: UserContext = Depends(get_current_user),
    facade: KpiQueryFacade = Depends(get_kpi_facade),
):
    """지정된 시뮬레이션 ID의 OEE, TEEP, FPY 등 제조 KPI를 산출하여 반환합니다."""
    result_dto = facade.calculate_oee(sim_id=sim_id, ctx=ctx)
    return GlobalResponseDto.success_response(data=result_dto)
