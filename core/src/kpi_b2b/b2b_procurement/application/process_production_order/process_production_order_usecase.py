from dataclasses import dataclass

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
from shared.events.domain_event_mapper import DomainEventMapper
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.ipc.event_bus import EventBus
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.audit.audit_event_type_enum import AuditEventType
from shared.security.audit.audit_events import AuditEvent
from shared.security.audit.audit_severity_enum import AuditSeverity
from shared.security.audit.global_audit_logger import GlobalAuditLogger
from shared.security.context_guard import require_user_context


@dataclass(frozen=True)
class ProductionOrderDispatchedDomainEvent:
    """생산 발주 발행 도메인 이벤트 페이로드"""

    order_id: str
    product_code: str
    target_quantity: int
    company_id: str
    factory_phase: str
    packml_state: str
    event_type: str = "PRODUCTION_ORDER_DISPATCHED"
    source_component: str = "B2BProcurement"


class ProcessProductionOrderUseCase:
    """생산 발주 생성, 자재 소진 검증 및 PackML 상태 전이를 처리하는 유스케이스"""

    def __init__(
        self,
        command_repo: IProcurementCommandRepository,
        system_logger: GlobalSystemLogger | None = None,
        audit_logger: GlobalAuditLogger | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._command_repo = command_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="ProcessProductionOrderUseCase"
        )
        self._audit_logger = audit_logger or GlobalAuditLogger()
        self._event_bus = event_bus

    @require_user_context
    def execute(
        self,
        request_dto: ProductionOrderRequestDto,
        ctx: UserContext,
    ) -> ProductionOrderResultDto:
        try:
            order = ProductionOrder.create(
                order_id=request_dto.order_id,
                product_code=request_dto.product_code,
                target_quantity=request_dto.target_quantity,
                company_id=ctx.company_id,
                factory_phase=FactoryPhase(request_dto.factory_phase),
            )

            inventory = MaterialInventory(
                material_code=f"MAT-{request_dto.product_code}",
                available_stock=10000.0,
                unit_per_product=2.5,
            )
            remaining_stock = inventory.check_and_consume(request_dto.target_quantity)

            order.transition_to_starting()
            order.transition_to_execute()

            self._command_repo.save(order)

        except ValueError as e:
            self._audit_logger.log(
                AuditEvent(
                    event_type=AuditEventType.DATA_ACCESS,
                    action="PROCESS_PRODUCTION_ORDER_REJECTED",
                    target=f"ProductCode:{request_dto.product_code}",
                    severity=AuditSeverity.WARNING,
                    user_ctx=ctx,
                    details={"reason": str(e), "quantity": request_dto.target_quantity},
                )
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        self._audit_logger.log(
            AuditEvent(
                event_type=AuditEventType.DATA_ACCESS,
                action="PROCESS_PRODUCTION_ORDER_DISPATCHED",
                target=f"ProductionOrder:{order.order_id}",
                severity=AuditSeverity.INFO,
                user_ctx=ctx,
                details={
                    "product_code": order.product_code,
                    "target_quantity": order.target_quantity,
                    "packml_state": order.packml_state.value,
                },
            )
        )

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

        # EventBus 이벤트 발행
        if self._event_bus:
            domain_event = ProductionOrderDispatchedDomainEvent(
                order_id=order.order_id,
                product_code=order.product_code,
                target_quantity=order.target_quantity,
                company_id=ctx.company_id,
                factory_phase=order.factory_phase.value,
                packml_state=order.packml_state.value,
            )
            integration_event = DomainEventMapper.to_integration_event(
                domain_event=domain_event,
                trace_id=getattr(ctx, "trace_id", "TRC-ORDER-DISPATCH"),
            )
            self._event_bus.publish(
                topic="procurement.order.dispatched",
                event=integration_event,
            )

        return ProductionOrderResultDto(
            order_id=order.order_id,
            packml_state=order.packml_state.value,
            factory_phase=order.factory_phase.value,
            remaining_material_stock=remaining_stock,
        )
