import pytest
from kpi_b2b.b2b_procurement.application.process_production_order.process_production_order_usecase import (
    ProcessProductionOrderUseCase,
)
from kpi_b2b.b2b_procurement.application.process_production_order.production_order_request_dto import (
    ProductionOrderRequestDto,
)
from shared.context.user_context import UserContext
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="USER_001",
        username="engineer",
        company_id="COMPANY_A",
        role=UserRole.FACTORY_MANAGER,
    )


@pytest.fixture
def usecase():
    return ProcessProductionOrderUseCase()


def test_production_order_baseline_happy_path(usecase, valid_ctx):
    req = ProductionOrderRequestDto(
        order_id="ORD-TEST-001",
        product_code="PRD-CNC-001",
        target_quantity=100,
        factory_phase="BASELINE",
    )
    result = usecase.execute(req, valid_ctx)

    assert result.order_id == "ORD-TEST-001"
    assert result.packml_state == "EXECUTE"
    assert result.factory_phase == "BASELINE"


def test_production_order_fms_optimized_happy_path(usecase, valid_ctx):
    req = ProductionOrderRequestDto(
        product_code="PRD-AMR-002",
        target_quantity=50,
        factory_phase="FMS_OPTIMIZED",
    )
    result = usecase.execute(req, valid_ctx)

    assert result.packml_state == "EXECUTE"
    assert result.factory_phase == "FMS_OPTIMIZED"


def test_production_order_insufficient_stock_error(usecase, valid_ctx):
    req = ProductionOrderRequestDto(
        product_code="PRD-HEAVY-003",
        target_quantity=50000,
        factory_phase="BASELINE",
    )

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(req, valid_ctx)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert exc_info.value.status_code == 400
