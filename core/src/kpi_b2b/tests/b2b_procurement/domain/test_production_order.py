import pytest
from kpi_b2b.b2b_procurement.domain.production_order.factory_phase_enum import (
    FactoryPhase,
)
from kpi_b2b.b2b_procurement.domain.production_order.material_inventory import (
    MaterialInventory,
)
from kpi_b2b.b2b_procurement.domain.production_order.production_order import (
    ProductionOrder,
)
from shared.enums.packml_state_enum import PackMLState


def test_tc_production_order_create_and_packml_state_machine():
    """발주 생성 및 PackML 상태 전이 (IDLE -> STARTING -> EXECUTE) 검증"""
    order = ProductionOrder.create(
        product_code="PRD-100",
        target_quantity=50,
        company_id="COMP-01",
        factory_phase=FactoryPhase.FMS_OPTIMIZED,
    )

    assert order.order_id.startswith("ORD-")
    assert order.factory_phase == FactoryPhase.FMS_OPTIMIZED
    assert order.packml_state == PackMLState.IDLE

    # 상태 전이
    order.transition_to_starting()
    assert order.packml_state == PackMLState.STARTING

    order.transition_to_execute()
    assert order.packml_state == PackMLState.EXECUTE


def test_tc_production_order_invalid_state_transition():
    """STARTING을 거치지 않고 바로 EXECUTE로 전이 시 예외 검증"""
    order = ProductionOrder.create(
        product_code="PRD-100",
        target_quantity=50,
        company_id="COMP-01",
        factory_phase=FactoryPhase.BASELINE,
    )

    with pytest.raises(ValueError, match="Cannot transition to EXECUTE"):
        order.transition_to_execute()


def test_tc_production_order_invalid_phase_type():
    """Enum이 아닌 타입(문자열 등) 전달 시 도메인 불변식 위반 검증"""
    with pytest.raises(ValueError, match="factory_phase must be a valid FactoryPhase"):
        ProductionOrder.create(
            product_code="PRD-100",
            target_quantity=50,
            company_id="COMP-01",
            factory_phase="INVALID_PHASE_NAME",  # type: ignore
        )


def test_tc_material_inventory_consumption():
    """자재 소진 계산 및 재고 부족 시 차단 검증"""
    inventory = MaterialInventory(
        material_code="MAT-PRD-100",
        available_stock=100.0,
        unit_per_product=2.0,
    )

    # 1. 정상 소진 (100 - (30 * 2.0) = 40.0)
    remaining = inventory.check_and_consume(order_quantity=30)
    assert remaining == 40.0
    assert inventory.available_stock == 40.0

    # 2. 재고 초과 소진 시도 시 예외 발생 및 재고 보존 검증 (40.0 < 25 * 2.0 = 50.0)
    with pytest.raises(ValueError, match="Insufficient material stock"):
        inventory.check_and_consume(order_quantity=25)
    assert inventory.available_stock == 40.0
