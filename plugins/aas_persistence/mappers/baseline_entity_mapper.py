from decimal import Decimal
from typing import Any, cast

from digital_twin.contracts.dtos.twin_baseline_dto import TwinBaselineDto
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_sync_status_enum import (
    TwinSyncStatus,
)

from plugins.aas_persistence.models.baseline_orm_model import BaselineOrmModel


class BaselineEntityMapper:
    """Domain Entity ↔ ORM Model ↔ Query DTO 상호 매퍼 (ACL)."""

    # --- Command Side (Entity ↔ ORM) ---
    @staticmethod
    def to_orm_model(baseline: TwinBaseline) -> BaselineOrmModel:
        sync_status_val = (
            baseline.sync_status.value
            if hasattr(baseline.sync_status, "value")
            else str(baseline.sync_status)
        )
        return BaselineOrmModel(
            baseline_id=baseline.baseline_id,
            company_id=baseline.company_id,
            baseline_name=baseline.baseline_name,
            sync_error_rate=Decimal(str(round(baseline.sync_error_rate, 4))),
            sync_status=sync_status_val,
            raw_sensor_summary=baseline.raw_sensor_summary or {},
            is_deleted=baseline.is_deleted,
        )

    @staticmethod
    def to_domain_entity(orm_model: BaselineOrmModel) -> TwinBaseline:
        raw_error_rate = cast(float | Decimal, orm_model.sync_error_rate)
        raw_sensor_summary = cast(dict[str, Any] | None, orm_model.raw_sensor_summary)
        sensor_summary: dict[str, float] = {
            str(k): float(v)
            for k, v in (raw_sensor_summary or {}).items()
            if isinstance(v, (int, float))
        }

        return TwinBaseline(
            baseline_id=str(orm_model.baseline_id),
            company_id=str(orm_model.company_id),
            baseline_name=str(orm_model.baseline_name),
            sync_error_rate=float(raw_error_rate),
            sync_status=TwinSyncStatus(str(orm_model.sync_status)),
            raw_sensor_summary=sensor_summary,
            is_deleted=bool(orm_model.is_deleted),
        )

    # --- Query Side (ORM → DTO) ---
    @staticmethod
    def to_dto(orm_model: BaselineOrmModel) -> TwinBaselineDto:
        raw_error_rate = cast(float | Decimal, orm_model.sync_error_rate)
        raw_sensor_summary = cast(dict[str, Any] | None, orm_model.raw_sensor_summary)
        sensor_summary_dict: dict[str, Any] = (
            dict(raw_sensor_summary) if raw_sensor_summary is not None else {}
        )

        return TwinBaselineDto(
            baseline_id=str(orm_model.baseline_id),
            company_id=str(orm_model.company_id),
            baseline_name=str(orm_model.baseline_name),
            sync_error_rate=float(raw_error_rate),
            sync_status=str(orm_model.sync_status),
            raw_sensor_summary=sensor_summary_dict,
            asset_mappings=(),
        )
