from dataclasses import dataclass


@dataclass(frozen=True)
class TurnkeyQuoteResponseDto:
    total_estimated_price: float
    delivery_days_estimated: int
