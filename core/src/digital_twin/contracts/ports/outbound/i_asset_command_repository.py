from typing import Protocol

from digital_twin.asset_library.domain.asset.asset import Asset


class IAssetCommandRepository(Protocol):
    """도메인 엔티티 상태 변경 및 영속화를 위한 Command Outbound Port"""

    def load_by_id(self, asset_id: str) -> Asset | None:
        """비즈니스 로직 수행 및 상태 수정을 위해 DB에서 엔티티를 복원(Reconstitution)합니다.
        대상이 없으면 None을 반환하며, 예외 발생 여부는 UseCase가 결정합니다.
        """
        ...

    def save(self, asset: Asset) -> None:
        """신규 생성된 엔티티를 등록하거나 변경된 엔티티 상태를 영속화(Upsert/Update)합니다.
        소프트 삭제는 엔티티의 is_deleted 상태 변경 후 save를 통해 영속화합니다.
        """
        ...

    def delete_by_id(self, asset_id: str) -> bool:
        """식별자 기반으로 영속성 저장소에서 물리 삭제(Hard Delete)를 수행합니다.
        반환값: 실제 삭제 성공 여부 (대상이 없어 삭제되지 않았으면 False)
        """
        ...
