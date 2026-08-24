from typing import Protocol


class IProcurementQueryRepository(Protocol):
    """B2B 조달 도메인 순수 데이터 조회(R) 포트"""

    def exists_by_id_and_company(
        self,
        baseline_id: str,
        company_id: str,
    ) -> bool:
        """해당 테넌트의 유효한 베이스라인 존재 여부 판별 (IDOR 방어)"""
        ...

    def get_production_order_by_id(
        self,
        baseline_id: str,
        company_id: str,
    ) -> str | None: ...
