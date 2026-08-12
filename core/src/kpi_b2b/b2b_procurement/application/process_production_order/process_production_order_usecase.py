"""
@file process_production_order_usecase.py
@description 생산 발주 명령 수신 후 원자재 차감, Real-to-Sim 정합성 검증 및 PackML 상태 전환 오케스트레이션 유즈케이스
"""

from typing import Any

from asset_twin.twin_reconstruction.domain.services.real_to_sim_validator import (
    RealToSimValidator,
)
from kpi_b2b.b2b_procurement.application.process_production_order.production_order_dto import (
    ProductionOrderRequestDto,
    ProductionOrderResultDto,
)
from kpi_b2b.b2b_procurement.domain.material_inventory import MaterialInventory
from kpi_b2b.b2b_procurement.domain.production_order import (
    FactoryPhaseEnum,
    ProductionOrder,
)
from shared.dtos.log_dtos import LogContext
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext


class ProcessProductionOrderUseCase:
    def __init__(
        self,
        inventory_repo: Any = None,
        logger: GlobalSystemLogger | None = None,
    ):
        self._inventory_repo = inventory_repo
        self._real_to_sim_validator = RealToSimValidator(tolerance_limit_percent=5.0)
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

        # 1. 도메인 엔티티 인스턴스화
        phase = FactoryPhaseEnum(request_dto.factory_phase)
        order = ProductionOrder.create_order(
            product_code=request_dto.product_code,
            target_quantity=request_dto.target_quantity,
            company_id=ctx.company_id,
            factory_phase=phase,
        )

        # 2. 원자재 재고 차감 검증
        inventory = MaterialInventory(
            material_code=f"MAT-{request_dto.product_code}",
            available_stock=10000.0,
            unit_per_product=2.5,
        )
        remaining_stock = inventory.check_and_consume(request_dto.target_quantity)

        # 3. FMS 도입 전/후 분기 처리
        is_real_to_sim_passed = True
        validation_details = None

        if phase == FactoryPhaseEnum.KAMP_BASELINE:
            # Step 1: Real-to-Sim 정합성 검증 수행
            kamp_mock = {
                "vibration_rms": 0.45,
                "temperature_celsius": 65.0,
                "yield_fpy_percent": 98.2,
            }
            sim_mock = {
                "vibration_rms": 0.46,
                "temperature_celsius": 65.8,
                "yield_fpy_percent": 97.9,
            }

            val_result = self._real_to_sim_validator.validate(kamp_mock, sim_mock)
            is_real_to_sim_passed = val_result.is_valid
            validation_details = val_result.details

            self._logger.info(
                f"KAMP Real-to-Sim validation finished. Passed: {is_real_to_sim_passed}, Overall Error: {val_result.overall_error_rate}%",
                log_ctx,
            )

        # 4. PackML 상태 전환 (IDLE -> STARTING -> EXECUTE)
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
            is_real_to_sim_passed=is_real_to_sim_passed,
            validation_details=validation_details,
        )
