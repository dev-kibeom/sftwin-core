from unittest.mock import MagicMock

import pytest
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.contracts.dtos.asset_dto import AssetDto
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from simulation.contracts.dtos.sim_result_dto import SimResultDto
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto
from simulation.contracts.ports.outbound.i_physics_engine import IPhysicsEngine
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_request_dto import (
    RunFmsSimulationRequestDto,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)
from simulation.fms_execution.domain.collision_detector import CollisionDetector


@pytest.fixture
def sample_asset_dto() -> AssetDto:
    return AssetDto(
        asset_id="ROBOT-01",
        asset_name="Test Robot",
        asset_type=AssetType.AMR,
        kinematics_metadata={
            "max_velocity_rad_per_sec": 3.14,
            "max_acceleration_rad_per_sec2": 6.28,
        },
    )


@pytest.fixture
def mock_physics_engine() -> MagicMock:
    return MagicMock(spec=IPhysicsEngine)


@pytest.fixture
def usecase(
    mock_physics_engine: MagicMock,
) -> RunFmsSimulationUseCase:
    return RunFmsSimulationUseCase(
        physics_engine=mock_physics_engine,
        collision_detector=CollisionDetector(),
    )


def test_tc_happy_path_run_fms_simulation(
    usecase: RunFmsSimulationUseCase,
    mock_physics_engine: MagicMock,
    sample_asset_dto: AssetDto,
    normal_trajectory_points: list[TrajectoryPointDto],
    standard_context: UserContext,
):
    """[TC-정상] DTO 기반 시나리오 생성 및 물리 엔진 궤적 연산 정상 완료 검증"""
    req_dto = RunFmsSimulationRequestDto(
        scenario_id="SCENARIO-100",
        baseline_id="BASE-100",
        assets=(sample_asset_dto,),
        task_waypoints=tuple(normal_trajectory_points),
    )

    mock_physics_engine.simulate_scenario.return_value = normal_trajectory_points

    result = usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert isinstance(result, SimResultDto)
    assert result.is_success is True
    assert result.collision_count == 0
    assert len(result.trajectory_points) == len(normal_trajectory_points)


def test_tc_edge_case_collision_detected(
    usecase: RunFmsSimulationUseCase,
    mock_physics_engine: MagicMock,
    sample_asset_dto: AssetDto,
    collided_trajectory_points: list[TrajectoryPointDto],
    standard_context: UserContext,
):
    """[TC-예외] 충돌 포인트 검출 시 ERR_SIM_COLLISION_DETECTED 발생 검증"""
    req_dto = RunFmsSimulationRequestDto(
        scenario_id="SCENARIO-COLLIDE",
        baseline_id="BASE-100",
        assets=(sample_asset_dto,),
    )

    mock_physics_engine.simulate_scenario.return_value = collided_trajectory_points

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_COLLISION_DETECTED
    assert exc_info.value.details == {"collision_count": 2}
