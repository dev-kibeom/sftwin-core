from typing import Protocol

from digital_twin.contracts.dtos.twin_baseline_dto import TwinBaselineDto


class IBaselineQueryRepository(Protocol):
    """트윈 베이스라인 화면 표출 및 통계 조회 Query Port"""

    def find_by_id(self, baseline_id: str, company_id: str) -> TwinBaselineDto | None:
        """테넌시 격리 및 논리 삭제 필터링이 적용된 DTO 단건 조회"""
        ...

    def exists_by_id_and_company(self, baseline_id: str, company_id: str) -> bool:
        """베이스라인 존재 여부 및 테넌시 소유권을 판별합니다."""
        ...
