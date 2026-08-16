"""
@file test_process_production_order.py
@description 생산 발주 및 PackML 상태 전환 유즈케이스 단위 테스트
"""

import pytest
from kpi_b2b.b2b_procurement.application.process_production_order.process_production_order_usecase import (
    ProcessProductionOrderUseCase,
)
from kpi_b2b.b2b_procurement.application.process_production_order.production_order_dto import (
    ProductionOrderRequestDto,
)
from shared.enums.user_role_enum import UserRoleEnum
from shared.context.user_context import UserContext


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="USER_001",
        username="engineer",
        company_id="COMPANY_A",
        role=UserRoleEnum.FACTORY_MANAGER,
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
