from decimal import Decimal
from typing import Any, cast

from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)

from plugins.aas_persistence.models.baseline_orm_model import BaselineOrmModel


class BaselineEntityMapper:
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
        return TwinBaseline(
            baseline_id=cast(str, orm_model.baseline_id),
            company_id=cast(str, orm_model.company_id),
            baseline_name=cast(str, orm_model.baseline_name),
            sync_error_rate=float(raw_error_rate),
            sync_status=cast(Any, orm_model.sync_status),
            raw_sensor_summary=cast(dict, orm_model.raw_sensor_summary) or {},
            is_deleted=bool(orm_model.is_deleted),
        )
