from enum import Enum


class B2bQuoteStatusEnum(str, Enum):
    REQUESTED = "REQUESTED"  # 견적 요청 완료 및 대기 중
    PROCESSED = "PROCESSED"  # 공급사 견적 산출 완료
    ACCEPTED = "ACCEPTED"  # 발주 확정 (결제 완료)
    REJECTED = "REJECTED"  # 견적 거절 또는 취소
