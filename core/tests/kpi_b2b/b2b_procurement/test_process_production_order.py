import unittest

from src.kpi_b2b.b2b_procurement.application.process_production_order.process_production_order_usecase import (
    ProcessProductionOrderUseCase,
)
from src.kpi_b2b.b2b_procurement.application.process_production_order.production_order_dto import (
    ProductionOrderRequestDto,
)
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.security.user_context import UserContext


class TestProcessProductionOrder(unittest.TestCase):
    def setUp(self):
        self.usecase = ProcessProductionOrderUseCase()
        self.valid_ctx = UserContext(
            user_id="USER_001",
            username="engineer",
            company_id="COMPANY_A",
            role=UserRoleEnum.FACTORY_MANAGER,
        )

    def test_production_order_kamp_baseline_happy_path(self):
        req = ProductionOrderRequestDto(
            product_code="PRD-CNC-001",
            target_quantity=100,
            factory_phase="KAMP_BASELINE",
        )
        result = self.usecase.execute(req, self.valid_ctx)

        self.assertEqual(result.packml_state, "EXECUTE")
        self.assertEqual(result.factory_phase, "KAMP_BASELINE")
        self.assertTrue(result.is_real_to_sim_passed)
        self.assertIsNotNone(result.validation_details)

    def test_production_order_fms_optimized_happy_path(self):
        req = ProductionOrderRequestDto(
            product_code="PRD-AMR-002",
            target_quantity=50,
            factory_phase="FMS_OPTIMIZED",
        )
        result = self.usecase.execute(req, self.valid_ctx)

        self.assertEqual(result.packml_state, "EXECUTE")
        self.assertEqual(result.factory_phase, "FMS_OPTIMIZED")


if __name__ == "__main__":
    unittest.main()
