from unittest.mock import MagicMock

import pytest
from kpi_b2b.b2b_procurement.application.process_production_order.process_production_order_usecase import (
    ProcessProductionOrderUseCase,
)
from kpi_b2b.b2b_procurement.application.process_production_order.production_order_request_dto import (
    ProductionOrderRequestDto,
)
from kpi_b2b.b2b_procurement.domain.production_order.factory_phase_enum import (
    FactoryPhase,
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
from shared.security.user_role_enum import UserRole


@pytest.fixture
def mock_command_repo() -> MagicMock:
    return MagicMock(spec=IProcurementCommandRepository)


@pytest.fixture
def usecase(mock_command_repo: MagicMock) -> ProcessProductionOrderUseCase:
    return ProcessProductionOrderUseCase(command_repo=mock_command_repo)


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


def test_tc_happy_path_process_production_order(
    usecase: ProcessProductionOrderUseCase,
    mock_command_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 생산 발주 생성, 원자재 차감, PackML 상태 전이(EXECUTE) 및 영속화 검증"""
    req_dto = ProductionOrderRequestDto(
        product_code="PRD-01",
        target_quantity=100,
        factory_phase=FactoryPhase.FMS_OPTIMIZED,
    )

    result = usecase.execute(request_dto=req_dto, ctx=standard_context)

    mock_command_repo.save_production_order.assert_called_once()
    saved_order = mock_command_repo.save_production_order.call_args[0][0]

    assert isinstance(result, ProductionOrderResultDto)
    assert result.packml_state == "EXECUTE"
    assert result.factory_phase == FactoryPhase.FMS_OPTIMIZED
    # 기본 가용 재고 10000.0 - (100 * 2.5) = 9750.0
    assert result.remaining_material_stock == 9750.0
    assert saved_order.company_id == "TEST-COMPANY-01"


def test_tc_edge_case_insufficient_material_stock(
    usecase: ProcessProductionOrderUseCase,
    mock_command_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-예외] 원자재 재고 부족 시 ERR_COMMON_INVALID_INPUT 발생 및 발주 저장 차단 검증"""
    # 5000 * 2.5 = 12500.0 (가용 재고 10000.0 초과)
    req_dto = ProductionOrderRequestDto(
        product_code="PRD-01",
        target_quantity=5000,
        factory_phase=FactoryPhase.FMS_OPTIMIZED,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert exc_info.value.status_code == 400
    mock_command_repo.save_production_order.assert_not_called()


def test_tc_edge_case_invalid_factory_phase_string(
    usecase: ProcessProductionOrderUseCase,
    mock_command_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-예외] 요청 DTO의 유효하지 않은 Phase 문자열이 400 ERR_COMMON_INVALID_INPUT으로 변환되는지 검증"""
    req_dto = ProductionOrderRequestDto(
        product_code="PRD-01",
        target_quantity=10,
        factory_phase="UNKNOWN_PHASE_STRING",
    )

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert exc_info.value.status_code == 400
    mock_command_repo.save_production_order.assert_not_called()
