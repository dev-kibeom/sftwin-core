from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Numeric, String

from plugins.aas_persistence.models.asset_orm_model import Base


class BaselineOrmModel(Base):
    __tablename__ = "twin_baselines"

    baseline_id = Column(String(64), primary_key=True, nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    baseline_name = Column(String(128), nullable=False)
    sync_error_rate = Column(Numeric(5, 4), nullable=False)
    sync_status = Column(String(32), nullable=False)
    raw_sensor_summary = Column(JSON, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
