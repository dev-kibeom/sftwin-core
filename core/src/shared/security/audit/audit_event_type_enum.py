from enum import Enum


class AuditEventType(str, Enum):
    """감사 이벤트 대분류"""

    SECURITY = "SECURITY"  # 인가 거부, 테넌트 침해, 인증 실패 등
    FAILSAFE = "FAILSAFE"  # E-Stop 발동, 토크 제한 초과, 충돌 감지 등
    DATA_ACCESS = "DATA_ACCESS"  # 민감 자산 열람 및 다운로드
