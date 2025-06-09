"""Data schemas for ETL pipeline"""
from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime
import re

class ProductSchema(BaseModel):
    """Product data validation schema"""
    platform: str = Field(..., description="E-commerce platform identifier")
    product_id: str = Field(..., min_length=1, description="Platform-specific product ID")
    name: str = Field(..., min_length=1, max_length=500, description="Product name")
    price: float = Field(..., ge=0, description="Current price in TWD")
    original_price: Optional[float] = Field(None, ge=0, description="Original/list price")
    url: str = Field(..., description="Product page URL")
    image_url: Optional[str] = Field(None, description="Product image URL")
    brand: Optional[str] = Field(None, max_length=100, description="Brand name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    availability: bool = Field(default=True, description="Product availability status")
    scraped_at: Optional[datetime] = Field(None, description="When data was scraped")
    
    @validator('platform')
    def validate_platform(cls, v):
        """Ensure platform is from our supported list"""
        allowed_platforms = ['pchome', 'momo', 'shopee', 'yahoo', 'ruten']
        if v.lower() not in allowed_platforms:
            raise ValueError(f'Platform must be one of: {allowed_platforms}')
        return v.lower()
    
    @validator('price', 'original_price')
    def validate_price_range(cls, v):
        """Validate price is within reasonable Taiwan market range"""
        if v is not None:
            if v < 0:
                raise ValueError('Price cannot be negative')
            if v > 10_000_000:  # 10 million TWD seems reasonable max
                raise ValueError('Price seems unreasonably high')
        return v
    
    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is properly formatted"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        # Basic URL pattern check
        url_pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v
    
    @validator('name')
    def clean_product_name(cls, v):
        """Clean and normalize product name"""
        # Remove extra whitespace
        v = ' '.join(v.split())
        # Remove common spam characters
        v = re.sub(r'[★☆⭐✨💎🔥💥]+', '', v)
        return v.strip()
    
    @validator('description')
    def clean_description(cls, v):
        """Clean product description"""
        if v:
            # Remove HTML tags if any
            v = re.sub(r'<[^>]+>', '', v)
            # Normalize whitespace
            v = ' '.join(v.split())
        return v
    
    class Config:
        from_attributes = True  # Changed from orm_mode = True
        json_schema_extra = {   # Changed from schema_extra
            "example": {
                "platform": "pchome",
                "product_id": "DYAJDQ-A900GNZX1",
                "name": "iPhone 15 (128GB)",
                "price": 22299.0,
                "original_price": 24900.0,
                "url": "https://24h.pchome.com.tw/prod/DYAJDQ-A900GNZX1",
                "brand": "Apple",
                "availability": True
            }
        }

class BulkProductSchema(BaseModel):
    """Schema for bulk product operations"""
    products: List[ProductSchema]
    source: str = Field(..., description="Source of the data (scraper name)")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('products')
    def validate_product_list(cls, v):
        """Ensure we have products and no duplicates"""
        if not v:
            raise ValueError('Product list cannot be empty')
        
        # Check for duplicates within the batch
        seen = set()
        for product in v:
            key = (product.platform, product.product_id)
            if key in seen:
                raise ValueError(f'Duplicate product found: {product.platform}:{product.product_id}')
            seen.add(key)
        
        return v