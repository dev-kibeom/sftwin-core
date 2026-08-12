"""
@file calculate_kpi_usecase.py
@description 표준 제조 KPI 연산을 조율하는 무상태 UseCase
"""

import uuid
from datetime import datetime, timezone

from kpi_b2b.kpi_dashboard.application.calculate_kpi.kpi_report_dto import (
    KpiReportDto,
)
from kpi_b2b.kpi_dashboard.domain.oee_calculator import OeeCalculator
from kpi_b2b.kpi_dashboard.ports.outbound.base_time_series_port import (
    BaseTimeSeriesPort,
)
from shared.dtos.log_dtos import LogContext
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger


class CalculateKpiUseCase:
    def __init__(
        self,
        ts_adapter: BaseTimeSeriesPort,
        logger: GlobalSystemLogger | None = None,
    ):
        self._ts_adapter = ts_adapter
        self._oee_calculator = OeeCalculator()
        self._logger = logger or GlobalSystemLogger(
            component_name="KpiDashboard_UseCase"
        )

    def execute(self, sim_id: str, company_id: str) -> KpiReportDto:
        log_ctx = LogContext(context={"sim_id": sim_id, "company_id": company_id})
        self._logger.info(
            f"Initiating KPI (OEE) calculation for simulation: {sim_id}", log_ctx
        )

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

        if not logs:
            self._logger.warn(f"No simulation logs found for {sim_id}", log_ctx)
            raise BaseSystemException(
                error_code="ERR_KPI_SIM_NOT_FOUND",
                message="종료되거나 유효하지 않은 시뮬레이션입니다.",
                status_code=404,
            )

        log_count = len(logs)
        (
            uptime,
            total_time,
            ideal_cycle_sum,
            actual_cycle_sum,
            good_count,
            total_count,
        ) = (
            0.0,
            0.0,
            0.0,
            0.0,
            0,
            0,
        )

        for log in logs:
            uptime += log.get("uptime", 0.0)
            total_time += log.get("total_time", 1.0)
            ideal_cycle_sum += log.get("ideal_cycle", 0.0)
            actual_cycle_sum += log.get("actual_cycle", 1.0)
            good_count += log.get("good_count", 0)
            total_count += log.get("total_count", 1)

        ideal_cycle = ideal_cycle_sum / log_count if log_count > 0 else 0.0
        actual_cycle = actual_cycle_sum / log_count if log_count > 0 else 1.0

        availability = self._oee_calculator.calculate_availability(uptime, total_time)
        performance = self._oee_calculator.calculate_performance(
            ideal_cycle, actual_cycle
        )
        quality = self._oee_calculator.calculate_quality(good_count, total_count)

        overall_oee = self._oee_calculator.compute_overall_oee(
            availability, performance, quality
        )
        teep = overall_oee * 0.85

        self._logger.info(
            f"Successfully computed OEE ({overall_oee:.4f}) for {sim_id}", log_ctx
        )

        return KpiReportDto(
            report_id=f"RPT-{uuid.uuid4()}",
            oee=round(overall_oee, 4),
            teep=round(teep, 4),
            fpy=round(quality, 4),
            generated_at=datetime.now(timezone.utc).isoformat(),
            estimated_roi_months=18.5,
        )
