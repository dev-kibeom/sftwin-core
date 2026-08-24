import pytest
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole
from simulation.layout_optimization.application.optimize_layout.optimize_layout_request_dto import (
    OptimizeLayoutRequestDto,
)
from simulation.layout_optimization.application.optimize_layout.optimize_layout_usecase import (
    OptimizeLayoutUseCase,
)


@pytest.fixture
def usecase() -> OptimizeLayoutUseCase:
    return OptimizeLayoutUseCase()


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


def test_tc_happy_path_optimize_layout(
    usecase: OptimizeLayoutUseCase, standard_context: UserContext
):
    """[TC-정상] 배치 최적화 요청 후 DTO 리스트 반환 검증"""
    req_dto = OptimizeLayoutRequestDto(
        assets=[{"asset_id": "CNC-01"}, {"asset_id": "ROBOT-01"}],
        canvas_bounds={"max_x": 60.0},
    )

    result = usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert len(result) == 2
    assert result[0].asset_id == "CNC-01"
    assert result[0].pos_x == 20.0
    assert result[1].asset_id == "ROBOT-01"
    assert result[1].pos_x == 40.0


def test_tc_edge_case_invalid_canvas_bounds(
    usecase: OptimizeLayoutUseCase, standard_context: UserContext
):
    """[TC-예외] 잘못된 Canvas 경계값 주입 시 400 ERR_COMMON_INVALID_INPUT 변환 검증"""
    req_dto = OptimizeLayoutRequestDto(
        assets=[{"asset_id": "CNC-01"}],
        canvas_bounds={"max_x": -5.0},
    )

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert exc_info.value.status_code == 400
