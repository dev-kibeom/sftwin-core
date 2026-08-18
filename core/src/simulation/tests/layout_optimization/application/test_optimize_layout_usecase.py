from unittest.mock import Mock

import pytest
from shared.context.user_context import UserContext
from shared.enums.user_role_enum import UserRoleEnum
from simulation.layout_optimization.application.optimize_layout.optimize_layout_dto import (
    OptimizeLayoutRequestDto,
)
from simulation.layout_optimization.application.optimize_layout.optimize_layout_usecase import (
    OptimizeLayoutUseCase,
)


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="usr-123",
        username="layout_planner",
        company_id="cmp-1",
        role=UserRoleEnum.FACTORY_MANAGER,
    )


def test_happy_path_optimize_layout_success(mock_logger, valid_ctx):
    """TC-정상: 설비 목록 좌표 배치 성공 및 DTO 변환 검증"""
    # Given
    usecase = OptimizeLayoutUseCase(mock_logger)
    assets = [
        {"asset_id": "ROBOT-ARM-1"},
        {"asset_id": "CONVEYOR-BELT-2"},
    ]
    request_dto = OptimizeLayoutRequestDto(
        assets=assets,
        canvas_bounds={"max_x": 60.0},
    )

    # When
    placements = usecase.execute(request_dto=request_dto, ctx=valid_ctx)

    # Then
    assert len(placements) == 2
    assert placements[0].asset_id == "ROBOT-ARM-1"
    assert placements[0].pos_x == 20.0
    assert placements[1].asset_id == "CONVEYOR-BELT-2"
    assert placements[1].pos_x == 40.0
