"""
[File Summary]
RunFmsSimulationUseCase (Stateless Singleton)
FMS 시뮬레이션 가동 흐름을 오케스트레이션합니다.
자원 한도 검증, IPC 물리 엔진 연산 호출, 충돌 검증의 순서로 실행되며 GTS 규격의 예외를 발생시킵니다.
"""

from datetime import datetime, timezone
from typing import Any

from src.shared.dtos.log_dtos import LogContext
from src.shared.dtos.sim_result_dto import SimResultDto

# GTS 및 공통 포트 의존성 (가정된 경로)
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.logging.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext
from src.simulation.fms_execution.domain.collision_detector import CollisionDetector
from src.simulation.fms_execution.domain.fms_scenario import FmsScenario


class RunFmsSimulationUseCase:
    # 4.2GB VRAM 제한 상수
    MAX_VRAM_CACHE_LIMIT_MB = 4200

    def __init__(self, physics_adapter, logger: GlobalSystemLogger):
        # DIP 준수: 구체적 C++ Adapter가 아닌 인터페이스 주입
        self._physics_adapter = physics_adapter
        self._logger = logger

    def execute(
        self,
        scenario_id: str,
        baseline_id: str,
        assets: list[dict[str, Any]],
        ctx: UserContext,
    ) -> SimResultDto:
        log_ctx = LogContext(trace_id=f"TRC-{scenario_id}")
        self._logger.info(
            f"FMS Simulation execution requested by {ctx.user_id}", log_ctx
        )

        # 1. 시나리오 메타데이터 유효성 검증 (Guard Clause)
        scenario = FmsScenario(
            scenario_id=scenario_id, baseline_id=baseline_id, assets=assets
        )
        if not scenario.validate_scenario():
            self._logger.warn("Invalid scenario metadata", log_ctx)
            raise BaseSystemException(
                error_code="ERR_SIM_INVALID_SCENARIO",
                message="AAS or Kinematics metadata schema violation or missing baseline_id.",
                status_code=400,
            )

        # 2. TIS 자원 제약 검증 (VRAM 4.2GB 통제)
        if not self._check_vram_resource_limit():
            self._logger.error("VRAM Resource exhausted", log_ctx)
            raise BaseSystemException(
                error_code="ERR_SIM_RESOURCE_EXHAUSTED",
                message="GPU VRAM cache exceeds the 4.2GB limit.",
                status_code=503,
            )

        # 3. C++ 물리 엔진 동역학 연산 호출 (IPC 통신)
        try:
            trajectory_results = self._physics_adapter.calculate_kinematics(scenario)
        except TimeoutError as exc:
            self._logger.error("IPC Sync timeout (>1ms)", log_ctx, exc=exc)
            raise BaseSystemException(
                error_code="ERR_SIM_IPC_TIMEOUT",
                message="POSIX Shared Memory IPC synchronization timeout exceeded 1ms.",
                status_code=500,
            )

        # 4. 물리적 충돌 및 교착 판별
        detector = CollisionDetector()
        if detector.detect(trajectory_results):
            self._logger.warn(
                f"Collision/Deadlock detected. Count: {detector.collision_count}",
                log_ctx,
            )
            raise BaseSystemException(
                error_code="ERR_SIM_COLLISION_DETECTED",
                message="Physical collision or Fleet deadlock detected during computation.",
                status_code=409,
            )

        # 5. 정상 완료 (COMPLETED)
        self._logger.info("FMS Simulation completed successfully", log_ctx)
        return SimResultDto(
            scenario_id=scenario_id,
            is_success=True,
            collision_count=detector.collision_count,
            estimated_cycle_time_sec=14.5,  # 예측 공정 시간 (임시 Mock 값)
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            trajectory_points=trajectory_results,
        )

    def _check_vram_resource_limit(self) -> bool:
        """
        단일 노드 워크스테이션의 GPU VRAM 할당량을 점검합니다.
        (본 예제에서는 인프라 모니터링 API 조회를 가정하여 항상 True 반환)
        """
        current_vram_usage_mb = 3500  # Mocking
        return current_vram_usage_mb <= self.MAX_VRAM_CACHE_LIMIT_MB
