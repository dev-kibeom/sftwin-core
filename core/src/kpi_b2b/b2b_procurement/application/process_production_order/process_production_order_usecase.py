from kpi_b2b.b2b_procurement.application.process_production_order.production_order_request_dto import (
    ProductionOrderRequestDto,
)
from kpi_b2b.b2b_procurement.domain.material_inventory import MaterialInventory
from kpi_b2b.b2b_procurement.domain.production_order import ProductionOrder
from kpi_b2b.ports.inbound.dtos.production_order_result_dto import (
    ProductionOrderResultDto,
)
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class ProcessProductionOrderUseCase:
    def __init__(
        self,
        command_repo: IProcurementCommandRepository | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ):
        self._command_repo = command_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="ProcessProductionOrderUseCase"
        )

    @require_user_context
    def execute(
        self, request_dto: ProductionOrderRequestDto, ctx: UserContext
    ) -> ProductionOrderResultDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-PROD-ORDER"),
            context={
                "product_code": request_dto.product_code,
                "quantity": request_dto.target_quantity,
                "phase": request_dto.factory_phase,
                "company_id": ctx.company_id,
            },
        )

        try:
            order = ProductionOrder.create_order(
                dto=request_dto, company_id=ctx.company_id
            )

            inventory = MaterialInventory(
                material_code=f"MAT-{request_dto.product_code}",
                available_stock=10000.0,
                unit_per_product=2.5,
            )
            remaining_stock = inventory.check_and_consume(request_dto.target_quantity)

            order.transition_to_starting()
            order.transition_to_execute()
        except ValueError as e:
            self._system_logger.warn(
                f"Production order validation failed: {str(e)}", log_ctx
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INVALID_INPUT,
                message=str(e),
                status_code=422,
            ) from e

        self._system_logger.info(
            f"Production order '{order.order_id}' successfully dispatched in EXECUTE state.",
            log_ctx,
        )

        return ProductionOrderResultDto(
            order_id=order.order_id,
            packml_state=order.packml_state.value,
            factory_phase=order.factory_phase.value,
            remaining_material_stock=remaining_stock,
        )
