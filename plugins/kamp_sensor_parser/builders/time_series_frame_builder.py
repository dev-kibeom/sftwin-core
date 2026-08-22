from typing import Any

from shared.context.log_context import LogContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

from plugins.kamp_sensor_parser.schemas.kinematics_frame_dto import KinematicsFrameDto


class TimeSeriesFrameBuilder:
    """순기구학(FK) 연산 결과와 시계열 데이터를 결합하여 불변 프레임 시계열을 패키징하는 전담 빌더 (FCN-KMP-005)"""

    REQUIRED_TIME_SERIES_KEYS = ("time", "x_pos", "y_pos", "z_pos")
    REQUIRED_FK_KEYS = ("joint_positions", "cartesian_poses", "quaternions")

    def __init__(
        self,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="TimeSeriesFrameBuilder"
        )

    def build_frames(
        self,
        time_series: dict[str, list[float]],
        fk_results: dict[str, list[Any]],
        sampling_rate_hz: float = 100.0,
    ) -> list[KinematicsFrameDto]:
        """[FCN-KMP-005 메인 진입점] 입력 데이터 정합성 검증, 시간 축 정렬, 프레임 DTO 생성 및 패키징 일괄 수행"""
        log_ctx = LogContext(
            trace_id="TRC-FRAME-BUILD",
            context={
                "sampling_rate_hz": sampling_rate_hz,
                "time_series_keys": list(time_series.keys()),
                "fk_keys": list(fk_results.keys()),
            },
        )
        self._system_logger.debug("Executing time-series frame packaging", log_ctx)

        # 1. 입력 유효성 및 배열 길이 정합성 검증
        total_samples = self._validate_frame_inputs(
            time_series=time_series,
            fk_results=fk_results,
            sampling_rate_hz=sampling_rate_hz,
            log_ctx=log_ctx,
        )

        # 2. 0.0s 기준 균등 타임스탬프 시간 축 정규화
        aligned_times = self._align_time_indices(
            time_list=time_series["time"],
            total_samples=total_samples,
            sampling_rate_hz=sampling_rate_hz,
        )

        # 3. 전체 타임스텝 프레임 DTO 패키징
        frames = self._pack_frame_series(
            aligned_times=aligned_times,
            joint_positions=fk_results["joint_positions"],
            cartesian_poses=fk_results["cartesian_poses"],
            quaternions=fk_results["quaternions"],
        )

        self._system_logger.info(
            f"Successfully built {len(frames)} kinematics frames at {sampling_rate_hz}Hz",
            log_ctx,
        )
        return frames

    # =========================================================================
    # Top-Down Private Helper Methods
    # =========================================================================

    def _validate_frame_inputs(
        self,
        time_series: dict[str, list[float]],
        fk_results: dict[str, list[Any]],
        sampling_rate_hz: float,
        log_ctx: LogContext,
    ) -> int:
        """샘플링 주기, 필수 키 유무 및 배열 간 길이 일치성 검증 (GTS 5절 표준 예외 적용)"""
        if sampling_rate_hz <= 0.0:
            self._system_logger.error(
                f"Invalid sampling rate: {sampling_rate_hz}. Must be > 0.0", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=f"Invalid sampling rate: {sampling_rate_hz}. Must be > 0.0",
            )

        # 필수 키 존재 검증
        for req_key in self.REQUIRED_TIME_SERIES_KEYS:
            if req_key not in time_series:
                self._system_logger.error(
                    f"Missing required time-series key: '{req_key}'", log_ctx
                )
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                    custom_message=f"Missing required time-series key: '{req_key}'",
                )

        for req_fk_key in self.REQUIRED_FK_KEYS:
            if req_fk_key not in fk_results:
                self._system_logger.error(
                    f"Missing required FK result key: '{req_fk_key}'", log_ctx
                )
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                    custom_message=f"Missing required FK result key: '{req_fk_key}'",
                )

        sample_count = len(time_series["time"])
        if sample_count == 0:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                custom_message="Time-series array is empty.",
            )

        # time_series 및 fk_results 내부 배열 길이 일치성 검증
        for key in self.REQUIRED_TIME_SERIES_KEYS:
            if len(time_series[key]) != sample_count:
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                    custom_message=(
                        f"Time series length mismatch: 'time' has {sample_count} items, "
                        f"but '{key}' has {len(time_series[key])} items."
                    ),
                )

        for fk_key in self.REQUIRED_FK_KEYS:
            if len(fk_results[fk_key]) != sample_count:
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
                    custom_message=(
                        f"FK results length mismatch: 'time' has {sample_count} items, "
                        f"but '{fk_key}' has {len(fk_results[fk_key])} items."
                    ),
                )

        return sample_count

    def _align_time_indices(
        self,
        time_list: list[float],
        total_samples: int,
        sampling_rate_hz: float,
    ) -> list[float]:
        """0.0s 기준 균등 타임스탬프 (dt = 1.0 / sampling_rate_hz) 정규화"""
        dt = 1.0 / sampling_rate_hz
        return [round(i * dt, 6) for i in range(total_samples)]

    def _create_single_frame(
        self,
        timestamp: float,
        joint_pos: tuple[float, ...],
        cartesian: dict[str, float],
        quat: dict[str, float],
    ) -> KinematicsFrameDto:
        """단일 타임스텝의 불변 KinematicsFrameDto 인스턴스 생성"""
        return KinematicsFrameDto(
            timestamp=timestamp,
            joint_positions=joint_pos,  # type: ignore[arg-type]
            cartesian_pose=cartesian,
            quaternion=quat,
        )

    def _pack_frame_series(
        self,
        aligned_times: list[float],
        joint_positions: list[tuple[float, ...]],
        cartesian_poses: list[dict[str, float]],
        quaternions: list[dict[str, float]],
    ) -> list[KinematicsFrameDto]:
        """N개 타임스텝을 순회하며 불변 프레임 리스트 조립"""
        frames: list[KinematicsFrameDto] = []
        for t, joints, cart, q in zip(
            aligned_times, joint_positions, cartesian_poses, quaternions, strict=True
        ):
            frame = self._create_single_frame(
                timestamp=t,
                joint_pos=joints,
                cartesian=cart,
                quat=q,
            )
            frames.append(frame)
        return frames
