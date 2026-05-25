from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VehicleCreate(BaseModel):
    brand: str = Field(..., max_length=100)
    location: str = Field(..., max_length=255)
    applicant: str = Field(..., max_length=255)
    year: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class VehicleUpdate(BaseModel):
    brand: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    applicant: Optional[str] = Field(None, max_length=255)
    year: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class VehicleResponse(BaseModel):
    id: str
    brand: str
    location: str
    applicant: str
    year: Optional[int]
    price: Optional[float]
    description: Optional[str]
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VehicleListResponse(BaseModel):
    items: list[VehicleResponse]
    total: int
