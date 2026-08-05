from typing import List
from pydantic import BaseModel, Field


class ItineraryRequest(BaseModel):
    destination: str = Field(..., description="e.g. Goa")
    days: int = Field(..., ge=1, le=30)
    budget: str = Field("moderate", description="economy / moderate / luxury")
    traveller_count: int = Field(1, ge=1, le=50)
    interests: List[str] = Field(default_factory=list)  # nature, historical, food...