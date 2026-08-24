from kpi_b2b.b2b_procurement.application.process_production_order.production_order_request_dto import (
    ProductionOrderRequestDto,
)
from kpi_b2b.b2b_procurement.domain.production_order.factory_phase_enum import (
    FactoryPhase,
)
from kpi_b2b.b2b_procurement.domain.production_order.material_inventory import (
    MaterialInventory,
)
from kpi_b2b.b2b_procurement.domain.production_order.production_order import (
    ProductionOrder,
)
from kpi_b2b.contracts.dtos.production_order_result_dto import (
    ProductionOrderResultDto,
)
from kpi_b2b.contracts.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class ProcessProductionOrderUseCase:
    """생산 발주 생성, 자재 소진 검증 및 PackML 상태 전이를 처리하는 유스케이스"""

    def __init__(
        self,
        command_repo: IProcurementCommandRepository,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._command_repo = command_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="ProcessProductionOrderUseCase"
        )

    @require_user_context
    def execute(
        self,
        request_dto: ProductionOrderRequestDto,
        ctx: UserContext,
    ) -> ProductionOrderResultDto:
        try:
            # 1. 도메인 엔티티 생성 (팩토리 메서드 위임)
            order = ProductionOrder.create(
                order_id=request_dto.order_id,
                product_code=request_dto.product_code,
                target_quantity=request_dto.target_quantity,
                company_id=ctx.company_id,
                factory_phase=FactoryPhase(request_dto.factory_phase),
            )

            # 2. 원자재 재고 검증 및 소진
            inventory = MaterialInventory(
                material_code=f"MAT-{request_dto.product_code}",
                available_stock=10000.0,
                unit_per_product=2.5,
            )
            remaining_stock = inventory.check_and_consume(request_dto.target_quantity)

            # 3. PackML 상태 전이 (IDLE -> STARTING -> EXECUTE)
            order.transition_to_starting()
            order.transition_to_execute()

            # 4. 저장소 영속화
            self._command_repo.save_production_order(order)

        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        # 5. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Production order '{order.order_id}' successfully dispatched in EXECUTE state.",
            extra={
                "order_id": order.order_id,
                "product_code": order.product_code,
                "target_quantity": order.target_quantity,
                "company_id": ctx.company_id,
                "remaining_stock": remaining_stock,
            },
        )

        return ProductionOrderResultDto(
            order_id=order.order_id,
            packml_state=order.packml_state.value,
            factory_phase=order.factory_phase.value,
            remaining_material_stock=remaining_stock,
        )
