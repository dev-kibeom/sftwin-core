from enum import Enum


class AuditSeverity(str, Enum):
    """감사 로그 위험도 등급"""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
