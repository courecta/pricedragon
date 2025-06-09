"""API response schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProductResponse(BaseModel):
    """Product response schema for API"""
    id: Optional[int] = None
    platform: str
    product_id: str
    name: str
    price: float
    original_price: Optional[float] = None
    url: str
    image_url: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    availability: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PriceHistoryResponse(BaseModel):
    """Price history response schema"""
    id: Optional[int] = None
    platform: str
    product_id: str
    price: float
    availability: bool
    scraped_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    """Search results response"""
    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool