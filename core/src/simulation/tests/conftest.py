import pytest
from shared.context.user_context import UserContext
from shared.security.user_role_enum import UserRole
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto


@pytest.fixture
def standard_context() -> UserContext:
    """공용 필드 엔지니어 컨텍스트"""
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


@pytest.fixture
def normal_trajectory_points() -> list[TrajectoryPointDto]:
    """충돌이 발생하지 않은 정상 궤적 데이터"""
    return [
        TrajectoryPointDto(
            time_sec=0.1,
            asset_id="ROBOT-01",
            position_x=0.0,
            position_y=0.0,
            position_z=0.0,
            velocity=1.0,
            is_collided=False,
        ),
        TrajectoryPointDto(
            time_sec=0.2,
            asset_id="ROBOT-01",
            position_x=1.0,
            position_y=1.0,
            position_z=1.0,
            velocity=1.0,
            is_collided=False,
        ),
    ]


@pytest.fixture
def collided_trajectory_points() -> list[TrajectoryPointDto]:
    """충돌 플래그가 포함된 결함 궤적 데이터"""
    return [
        TrajectoryPointDto(
            time_sec=0.1,
            asset_id="ROBOT-01",
            position_x=1.0,
            position_y=1.0,
            position_z=1.0,
            velocity=0.5,
            is_collided=True,
        ),
        TrajectoryPointDto(
            time_sec=0.2,
            asset_id="ROBOT-01",
            position_x=1.2,
            position_y=1.2,
            position_z=1.2,
            velocity=0.5,
            is_collided=False,
        ),
        TrajectoryPointDto(
            time_sec=0.3,
            asset_id="ROBOT-02",
            position_x=1.2,
            position_y=1.2,
            position_z=1.2,
            velocity=0.5,
            is_collided=True,
        ),
    ]
