from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AssetOrmModel(Base):
    """MySQL assets 테이블 ORM 매핑 모델."""

    __tablename__ = "assets"

    asset_id = Column(String(64), primary_key=True, nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    asset_name = Column(String(128), nullable=False)
    asset_type = Column(String(32), nullable=False)
    kinematics_metadata = Column(JSON, nullable=False)
    cad_file_path = Column(String(255), nullable=True)
    aas_file_path = Column(String(255), nullable=False)
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
