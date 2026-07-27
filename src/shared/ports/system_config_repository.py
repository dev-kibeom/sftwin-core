from abc import ABC, abstractmethod


class SystemConfigEntity:
    """system_configs 공유 DB 엔티티 표현"""

    def __init__(
        self,
        config_key: str,
        config_value: str,
        description: str,
        updated_at: str,
        is_deleted: int = 0,
    ):
        self.config_key = config_key
        self.config_value = config_value
        self.description = description
        self.updated_at = updated_at
        self.is_deleted = is_deleted


class SystemConfigRepository(ABC):
    """공통 시스템 설정 데이터 접근 포트 추상 인터페이스 (DIP 준수)"""

    @abstractmethod
    def find_by_key(self, config_key: str) -> SystemConfigEntity | None:
        """설정 키로 DB 레코드 조회 (is_deleted = 0 조건 필수)"""
        pass
