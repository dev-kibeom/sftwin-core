"""
@file process_production_order_usecase.py
@description 생산 발주 접수, 원자재 재고 차감 및 주문 상태 전이를 총괄하는 단일 책임 유즈케이스
"""

from kpi_b2b.b2b_procurement.application.process_production_order.production_order_dto import (
    ProductionOrderRequestDto,
    ProductionOrderResultDto,
)
from kpi_b2b.b2b_procurement.domain.material_inventory import MaterialInventory
from kpi_b2b.b2b_procurement.domain.production_order import ProductionOrder
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from shared.logger.system_logger.log_context import LogContext
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext


class ProcessProductionOrderUseCase:
    def __init__(
        self,
        command_repo: IProcurementCommandRepository | None = None,
        logger: GlobalSystemLogger | None = None,
    ):
        self._command_repo = command_repo
        self._logger = logger or GlobalSystemLogger(
            component_name="ProcessProductionOrderUseCase"
        )

    def execute(
        self, request_dto: ProductionOrderRequestDto, ctx: UserContext
    ) -> ProductionOrderResultDto:
        log_ctx = LogContext(
            context={
                "product_code": request_dto.product_code,
                "quantity": request_dto.target_quantity,
                "phase": request_dto.factory_phase,
                "company_id": ctx.company_id,
            }
        )
        self._logger.info("Processing production order request.", log_ctx)

        # 1. DTO와 UserContext 기반 도메인 엔티티 생성
        order = ProductionOrder.create_order(dto=request_dto, ctx=ctx)

        # 2. 원자재 재고 차감 (비즈니스 규칙 검증)
        inventory = MaterialInventory(
            material_code=f"MAT-{request_dto.product_code}",
            available_stock=10000.0,
            unit_per_product=2.5,
        )
        remaining_stock = inventory.check_and_consume(request_dto.target_quantity)

        # 3. PackML 상태 전이 (IDLE -> STARTING -> EXECUTE)
        order.transition_to_starting()
        order.transition_to_execute()

        self._logger.info(
            f"Production order '{order.order_id}' successfully dispatched in EXECUTE state.",
            log_ctx,
        )

        return ProductionOrderResultDto(
            order_id=order.order_id,
            packml_state=order.packml_state.value,
            factory_phase=order.factory_phase.value,
            remaining_material_stock=remaining_stock,
        )
