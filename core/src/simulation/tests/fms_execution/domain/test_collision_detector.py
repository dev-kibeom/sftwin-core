from simulation.fms_execution.domain.collision_detector import (
    CollisionDetector,
    TrajectoryPoint,
)


def test_tc_collision_detector_no_collisions(
    normal_trajectory_points: list[TrajectoryPoint],
):
    """충돌 포인트가 없을 때 정상 판별 검증"""
    res = CollisionDetector.detect(normal_trajectory_points)
    assert res.is_collided is False
    assert res.collision_count == 0


def test_tc_collision_detector_with_collisions(
    collided_trajectory_points: list[TrajectoryPoint],
):
    """충돌 포인트 감지 및 카운트 집계 검증"""
    res = CollisionDetector.detect(collided_trajectory_points)
    assert res.is_collided is True
    assert res.collision_count == 2
