from pydantic import BaseModel, Field


class TurnkeyQuoteResponseDto(BaseModel):
    total_estimated_price: float = Field(..., gt=0)
    delivery_days_estimated: int = Field(..., ge=1)
