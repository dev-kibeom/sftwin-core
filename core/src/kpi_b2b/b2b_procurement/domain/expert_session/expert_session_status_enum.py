from enum import Enum


class ExpertSessionStatus(str, Enum):
    """비대면 전문가 상담 세션의 생명주기 상태"""

    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
