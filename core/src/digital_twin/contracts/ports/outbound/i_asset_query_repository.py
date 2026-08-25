from collections.abc import Sequence
from typing import Protocol

from digital_twin.contracts.dtos.asset_dto import (
    AssetDetailDto,
    AssetFilterDto,
    AssetSummaryDto,
)


class IAssetQueryRepository(Protocol):
    """화면/API 데이터 프로젝션 및 고속 조회를 위한 Query Outbound Port"""

    def get_by_id(self, asset_id: str, company_id: str) -> AssetDetailDto:
        """단건 상세 데이터를 조회하며, 데이터 부재 시 즉시 예외를 발생시킵니다."""
        ...

    def find_by_id(self, asset_id: str, company_id: str) -> AssetDetailDto | None:
        """단건 상세 데이터를 안전하게 조회합니다. (대상이 없거나 테넌시 불일치 시 None)"""
        ...

    def list_by_filter(
        self, filter_dto: AssetFilterDto, company_id: str
    ) -> Sequence[AssetSummaryDto]:
        """조건 검색 및 페이징 필터를 적용하여 목록용 요약 DTO 리스트를 조회합니다."""
        ...

    def exists_by_id_and_company(self, asset_id: str, company_id: str) -> bool:
        """본문 로드 없이 대상 존재 여부 및 테넌시 소유권만 빠르게 판별합니다. (SELECT 1)"""
        ...

    def count_by_filter(self, filter_dto: AssetFilterDto, company_id: str) -> int:
        """조건에 부합하는 총 레코드 수를 집계합니다. (COUNT 쿼리)"""
        ...
