"""
@file calculate_kpi_usecase.py
@description 표준 제조 KPI 연산을 조율하는 무상태 UseCase
"""

import uuid
from datetime import datetime, timezone

from src.kpi_b2b.kpi_dashboard.adapters.base_time_series_port import BaseTimeSeriesPort
from src.kpi_b2b.kpi_dashboard.domain.oee_calculator import OeeCalculator
from src.kpi_b2b.kpi_dashboard.dtos.kpi_report_dto import KpiReportDto
from src.shared.dtos.log_dtos import LogContext
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.logging.global_system_logger import GlobalSystemLogger


class CalculateKpiUseCase:
    def __init__(self, ts_adapter: BaseTimeSeriesPort):
        self._ts_adapter = ts_adapter
        self._oee_calculator = OeeCalculator()

        # GTS 4.2 JSON 구조화 시스템 로깅 규약 적용
        self._logger = GlobalSystemLogger()
        self._logger.component_name = "KpiDashboard_UseCase"

    def execute(self, sim_id: str, company_id: str) -> KpiReportDto:
        log_ctx = LogContext(context={"sim_id": sim_id, "company_id": company_id})
        self._logger.info(
            f"Initiating KPI (OEE) calculation for simulation: {sim_id}", log_ctx
        )

        # 1. 시뮬레이션 로그 조회 및 타임아웃(DB 예외) 처리 Guard
        try:
            logs = self._ts_adapter.fetch_simulation_logs(sim_id)
        except Exception as e:
            log_ctx.exc = e
            self._logger.error(
                "Database query timeout or internal failure while fetching simulation logs.",
                log_ctx,
            )
            raise BaseSystemException(
                error_code="ERR_KPI_DB_TIMEOUT",
                message="데이터베이스 쿼리 시간 초과 또는 내부 오류 발생.",
                status_code=500,
            )

        # 2. 시뮬레이션 로그 존재 유무 Guard
        if not logs:
            self._logger.warn(f"No simulation logs found for {sim_id}", log_ctx)
            raise BaseSystemException(
                error_code="ERR_KPI_SIM_NOT_FOUND",
                message="종료되거나 유효하지 않은 시뮬레이션입니다.",
                status_code=404,
            )

        # 3. 데이터 파싱 (시뮬레이션 로그 내 누적 데이터 모사)
        # (실제 환경에서는 logs 배열 기반 Map-Reduce 수행)
        uptime = sum(log.get("uptime", 0.0) for log in logs)
        total_time = sum(log.get("total_time", 1.0) for log in logs)
        ideal_cycle = sum(log.get("ideal_cycle", 0.0) for log in logs) / len(logs)
        actual_cycle = sum(log.get("actual_cycle", 1.0) for log in logs) / len(logs)
        good_count = sum(log.get("good_count", 0) for log in logs)
        total_count = sum(log.get("total_count", 1) for log in logs)

        # 4. 순수 도메인 로직 (OeeCalculator) 위임
        availability = self._oee_calculator.calculate_availability(uptime, total_time)
        performance = self._oee_calculator.calculate_performance(
            ideal_cycle, actual_cycle
        )
        quality = self._oee_calculator.calculate_quality(good_count, total_count)

        overall_oee = self._oee_calculator.compute_overall_oee(
            availability, performance, quality
        )
        teep = overall_oee * 0.85  # TEEP 임의 보정 로직 (가동률 반영)

        self._logger.info(
            f"Successfully computed OEE ({overall_oee:.4f}) for {sim_id}", log_ctx
        )

        # 5. DTO 조립 및 반환
        return KpiReportDto(
            report_id=f"RPT-{uuid.uuid4()}",
            oee=round(overall_oee, 4),
            teep=round(teep, 4),
            fpy=round(quality, 4),
            generated_at=datetime.now(timezone.utc).isoformat(),
            estimated_roi_months=18.5,  # ROI 산출 모델 적용 (stub)
        )
