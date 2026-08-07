import os
from fastapi import Request

from src.kpi_b2b.b2b_procurement.adapters.b2b_marketplace_adapter import (
    B2bMarketplaceAdapter,
)
from src.kpi_b2b.b2b_procurement.application.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from src.kpi_b2b.b2b_procurement.application.layout_mirroring_usecase import (
    LayoutMirroringUseCase,
)
from src.kpi_b2b.facades.kpi_query_facade import KpiQueryFacade, KpiQueryFacadeImpl
from src.kpi_b2b.facades.procurement_command_facade import (
    ProcurementCommandFacade,
    ProcurementCommandFacadeImpl,
)
from src.kpi_b2b.kpi_dashboard.adapters.influxdb_timeseries_adapter import (
    InfluxDbTimeSeriesAdapter,
)
from src.kpi_b2b.kpi_dashboard.application.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from src.shared.adapters.redis_cache_adapter import RedisCacheAdapter
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.security.jwt_auth_interceptor import JwtAuthInterceptor
from src.shared.security.rbac_authorization_manager import RbacAuthorizationManager
from src.shared.security.user_context import UserContext

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "SF-Twin-Development-Secret-Key-2026")
jwt_interceptor = JwtAuthInterceptor(jwt_secret_key=JWT_SECRET_KEY)
rbac_manager = RbacAuthorizationManager()

# Adapters wiring (Phase 3에서 실체화)
ts_adapter = InfluxDbTimeSeriesAdapter(client=None)
b2b_adapter = B2bMarketplaceAdapter(api_client=None)
redis_adapter = RedisCacheAdapter(redis_client=None)
mock_mysql_repo = None

# UseCases
calculate_kpi_uc = CalculateKpiUseCase(ts_adapter=ts_adapter)
generate_quote_uc = GenerateQuoteUseCase(
    b2b_adapter=b2b_adapter, mysql_repo=mock_mysql_repo
)
mirroring_uc = LayoutMirroringUseCase(mysql_repo=mock_mysql_repo)

# Singleton Facades
_kpi_facade_instance = KpiQueryFacadeImpl(
    calculate_kpi_uc=calculate_kpi_uc,
    rbac_manager=rbac_manager,
    sim_repo=mock_mysql_repo,
)

_procurement_facade_instance = ProcurementCommandFacadeImpl(
    generate_quote_uc=generate_quote_uc,
    mirroring_uc=mirroring_uc,
    redis_adapter=redis_adapter,
    rbac_manager=rbac_manager,
    baseline_repo=mock_mysql_repo,
)


def get_current_user(request: Request) -> UserContext:
    """HTTP 헤더에서 Bearer JWT 토큰을 추출하고 UserContext를 주입합니다. (개발/테스트 모킹 토큰 지원)"""
    auth_header = request.headers.get("Authorization") or request.headers.get(
        "authorization"
    )
    if not auth_header or "mock-test-token" in auth_header:
        return UserContext(
            user_id="DEV_ENGINEER_001",
            username="dev_engineer",
            company_id="SYSTEM",
            role=UserRoleEnum.SYSTEM_ADMIN,
            accessible_factory_ids=["BASE-001"],
        )
    return jwt_interceptor.intercept(dict(request.headers))


def get_kpi_facade() -> KpiQueryFacade:
    return _kpi_facade_instance


def get_procurement_facade() -> ProcurementCommandFacade:
    return _procurement_facade_instance
