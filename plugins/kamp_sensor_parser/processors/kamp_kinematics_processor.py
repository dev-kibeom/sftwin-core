from typing import Any

import numpy as np
from shared.context.log_context import LogContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger


class KampKinematicsProcessor:
    """정제된 시계열 기반 관절 각도 역산 및 순기구학(FK)/3D 쿼터니언 변환 전담 프로세서 (FCN-KMP-004)"""

    REQUIRED_AXIS_KEYS = ("time", "x_pos", "y_pos", "z_pos")

    def __init__(
        self,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="KampKinematicsProcessor"
        )

    def compute_fk(
        self, time_series_data: dict[str, list[float]]
    ) -> dict[str, list[Any]]:
        """[FCN-KMP-004 메인 진입점] 시계열 정합성 검증, 관절각 역산, FK 및 쿼터니언 변환 일괄 수행"""
        log_ctx = LogContext(
            trace_id="TRC-KAMP-FK-COMPUTE",
            context={"keys": list(time_series_data.keys())},
        )
        self._system_logger.debug("Executing forward kinematics computation", log_ctx)

        # 1. 시계열 데이터 무결성 검증
        total_samples = self._validate_series_integrity(time_series_data, log_ctx)

        x_pos = time_series_data["x_pos"]
        y_pos = time_series_data["y_pos"]
        z_pos = time_series_data["z_pos"]
        s_pos = time_series_data.get("s_pos")

        # 2. 6축 조인트 각도(rad) 벡터화 역산
        joint_positions = self._solve_joint_angles(
            x_pos=x_pos,
            y_pos=y_pos,
            z_pos=z_pos,
            s_pos=s_pos,
            total_samples=total_samples,
        )

        # 3. 엔드이펙터 3D 좌표 및 회전 유닛 쿼터니언 일괄 산출
        cartesian_poses, quaternions = self._compute_cartesian_and_quaternions(
            x_pos=x_pos,
            y_pos=y_pos,
            z_pos=z_pos,
            joint_positions=joint_positions,
        )

        # 4. 결과 딕셔너리 조립 및 반환
        return self._assemble_kinematics_result(
            joint_positions=joint_positions,
            cartesian_poses=cartesian_poses,
            quaternions=quaternions,
        )

    # =========================================================================
    # Top-Down Private Helper Methods
    # =========================================================================

    def _validate_series_integrity(
        self, time_series_data: dict[str, list[float]], log_ctx: LogContext
    ) -> int:
        """필수 키 존재 여부 및 모든 시계열 배열 길이의 동일성 검증 (GTS 표준 BaseSystemException 적용)"""
        for req_key in self.REQUIRED_AXIS_KEYS:
            if req_key not in time_series_data:
                self._system_logger.error(
                    f"Missing required time-series axis key: '{req_key}'", log_ctx
                )
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                    custom_message=f"Missing required time-series axis key: '{req_key}'",
                )

        lengths = {key: len(time_series_data[key]) for key in self.REQUIRED_AXIS_KEYS}
        sample_count = lengths["time"]

        if sample_count == 0:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message="Time-series dataset contains 0 samples.",
            )

        for key, length in lengths.items():
            if length != sample_count:
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                    custom_message=(
                        f"Series length mismatch: 'time' has {sample_count} items, "
                        f"but '{key}' has {length} items."
                    ),
                )

        # 선택 키(s_pos, feedrate) 존재 시 길이 일치 검증
        for opt_key in ("s_pos", "feedrate"):
            if (
                opt_key in time_series_data
                and len(time_series_data[opt_key]) != sample_count
            ):
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                    custom_message=(
                        f"Optional series length mismatch: 'time' has {sample_count} items, "
                        f"but '{opt_key}' has {len(time_series_data[opt_key])} items."
                    ),
                )

        return sample_count

    def _solve_joint_angles(
        self,
        x_pos: list[float],
        y_pos: list[float],
        z_pos: list[float],
        s_pos: list[float] | None,
        total_samples: int,
    ) -> list[tuple[float, float, float, float, float, float]]:
        """직교 위치 및 스핀들 각도를 기반으로 6개 관절 회전 각도(rad) 벡터화 계산"""
        np_x = np.asarray(x_pos, dtype=np.float64)
        np_y = np.asarray(y_pos, dtype=np.float64)
        np_z = np.asarray(z_pos, dtype=np.float64)

        if s_pos is not None:
            np_s = np.asarray(s_pos, dtype=np.float64)
        else:
            np_s = np.zeros(total_samples, dtype=np.float64)

        theta_1 = np.where((np_x == 0.0) & (np_y == 0.0), 0.0, np.arctan2(np_y, np_x))
        theta_2 = np.clip(np_z / 1000.0, -np.pi, np.pi)
        theta_3 = np.clip(np.sqrt(np_x**2 + np_y**2) / 1000.0, -np.pi, np.pi)
        theta_4 = np.zeros(total_samples, dtype=np.float64)
        theta_5 = np.zeros(total_samples, dtype=np.float64)
        theta_6 = np.deg2rad(np_s % 360.0)

        joint_matrix = np.column_stack(
            (theta_1, theta_2, theta_3, theta_4, theta_5, theta_6)
        )

        return [
            (
                float(row[0]),
                float(row[1]),
                float(row[2]),
                float(row[3]),
                float(row[4]),
                float(row[5]),
            )
            for row in joint_matrix
        ]

    def _compute_cartesian_and_quaternions(
        self,
        x_pos: list[float],
        y_pos: list[float],
        z_pos: list[float],
        joint_positions: list[tuple[float, float, float, float, float, float]],
    ) -> tuple[list[dict[str, float]], list[dict[str, float]]]:
        """엔드이펙터 3D 좌표 및 오일러 각으로부터 단위 쿼터니언(x, y, z, w, ||q||=1.0) 일괄 산출"""
        cartesian_poses = [
            {"x": float(x), "y": float(y), "z": float(z)}
            for x, y, z in zip(x_pos, y_pos, z_pos, strict=True)
        ]

        quaternions: list[dict[str, float]] = []

        for joint_tuple in joint_positions:
            yaw = joint_tuple[0]
            pitch = joint_tuple[1]
            roll = joint_tuple[5]

            cy = np.cos(yaw * 0.5)
            sy = np.sin(yaw * 0.5)
            cp = np.cos(pitch * 0.5)
            sp = np.sin(pitch * 0.5)
            cr = np.cos(roll * 0.5)
            sr = np.sin(roll * 0.5)

            qw = cr * cp * cy + sr * sp * sy
            qx = sr * cp * cy - cr * sp * sy
            qy = cr * sp * cy + sr * cp * sy
            qz = cr * cp * sy - sr * sp * cy

            norm = np.sqrt(qx**2 + qy**2 + qz**2 + qw**2)
            if norm > 0.0:
                qx /= norm
                qy /= norm
                qz /= norm
                qw /= norm
            else:
                qx, qy, qz, qw = 0.0, 0.0, 0.0, 1.0

            quaternions.append(
                {
                    "x": float(np.round(qx, 6)),
                    "y": float(np.round(qy, 6)),
                    "z": float(np.round(qz, 6)),
                    "w": float(np.round(qw, 6)),
                }
            )

        return cartesian_poses, quaternions

    def _assemble_kinematics_result(
        self,
        joint_positions: list[tuple[float, float, float, float, float, float]],
        cartesian_poses: list[dict[str, float]],
        quaternions: list[dict[str, float]],
    ) -> dict[str, list[Any]]:
        """Core 및 상위 프레임 빌더가 즉시 소비할 수 있는 불변 딕셔너리 구조로 조립"""
        return {
            "joint_positions": joint_positions,
            "cartesian_poses": cartesian_poses,
            "quaternions": quaternions,
        }
