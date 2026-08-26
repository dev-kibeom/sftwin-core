"""
@file kpi_report_dto.py
@description 시뮬레이션 및 실시간 계측 데이터 기반 제조 지표 및 ROI 정량 산출 DTO
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class KpiReportDto:
    report_id: str
    oee: float
    teep: float
    fpy: float
    generated_at: str
    estimated_roi_months: float | None = None
