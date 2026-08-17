from dataclasses import dataclass


@dataclass(frozen=True)
class B2bQuoteDto:
    quote_id: str
    total_estimated_price: float
    status: str
    delivery_days_estimated: int
