"""
@file b2b_quote_dto.py
@description B2B 마켓플레이스 응답 및 API 반환용 DTO
"""

from dataclasses import dataclass


@dataclass
class B2bQuoteDto:
    quote_id: str
    total_estimated_price: float
    status: str
    delivery_days_estimated: int
