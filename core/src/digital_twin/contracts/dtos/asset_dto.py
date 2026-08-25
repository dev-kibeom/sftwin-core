from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AssetDetailDto:
    """자산 단건 상세 조회 전용 불변 DTO (순수 원시 타입 기반)"""

    asset_id: str
    company_id: str
    asset_name: str
    asset_type: str  # Enum 의존성 제거 -> str
    cad_file_path: str | None = None
    kinematics_metadata: dict[str, Any] = field(default_factory=dict)
    submodels: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass(frozen=True)
class AssetSummaryDto:
    """자산 목록 조회 전용 요약 DTO"""

    asset_id: str
    company_id: str
    asset_name: str
    asset_type: str  # Enum 의존성 제거 -> str
    cad_file_path: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass(frozen=True)
class AssetFilterDto:
    """자산 조건 검색 및 페이징 필터 DTO"""

    asset_type: str | None = None  # str 기반 필터
    asset_name_keyword: str | None = None
    limit: int = 50
    offset: int = 0


# 호환용 Alias
AssetDto = AssetDetailDto
