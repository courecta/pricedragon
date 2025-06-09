"""
PriceDragon Database Models
Robust schema for multi-platform product data
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib

Base = declarative_base()

class Platform(Base):
    """E-commerce platforms (PChome, Momo, Yahoo, etc.)"""
    __tablename__ = 'platforms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # 'pchome', 'momo', 'yahoo'
    display_name = Column(String(100), nullable=False)     # 'PChome線上購物', 'momo購物網'
    base_url = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="platform")
    price_histories = relationship("PriceHistory", back_populates="platform")

class Category(Base):
    """Product categories for organization"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)  # 'Electronics', 'Fashion'
    name_zh = Column(String(100))                            # '電子產品', '時尚'
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for subcategories
    subcategories = relationship("Category", backref="parent", remote_side=[id])
    products = relationship("Product", back_populates="category")

class Product(Base):
    """Unified product catalog across all platforms"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    
    # Core product info
    name = Column(String(500), nullable=False)
    normalized_name = Column(String(500), nullable=False)  # Cleaned version for matching
    description = Column(Text)
    brand = Column(String(100))
    model = Column(String(200))
    
    # Platform-specific info
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=False)
    platform_product_id = Column(String(100), nullable=False)  # Original platform ID
    url = Column(String(1000))
    image_url = Column(String(1000))
    
    # Category
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    # Current pricing
    current_price = Column(Float)
    original_price = Column(Float)
    discount_percentage = Column(Float)
    currency = Column(String(10), default='TWD')
    
    # Availability
    is_available = Column(Boolean, default=True)
    stock_status = Column(String(50))  # 'in_stock', 'low_stock', 'out_of_stock'
    
    # Quality metrics
    data_quality_score = Column(Float, default=1.0)  # 0-1 score for data completeness
    last_scraped = Column(DateTime, default=datetime.utcnow)
    scrape_count = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    platform = relationship("Platform", back_populates="products")
    category = relationship("Category", back_populates="products")
    price_histories = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    product_matches = relationship("ProductMatch", foreign_keys="ProductMatch.product_a_id")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_platform_product', 'platform_id', 'platform_product_id'),
        Index('idx_normalized_name', 'normalized_name'),
        Index('idx_brand_model', 'brand', 'model'),
        Index('idx_last_scraped', 'last_scraped'),
    )
    
    def generate_hash_id(self):
        """Generate consistent hash ID for deduplication"""
        source = f"{self.platform_id}_{self.platform_product_id}_{self.normalized_name}"
        return hashlib.md5(source.encode()).hexdigest()

class PriceHistory(Base):
    """Track price changes over time"""
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=False)
    
    # Price data
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    discount_percentage = Column(Float)
    currency = Column(String(10), default='TWD')
    
    # Context
    availability = Column(Boolean, default=True)
    stock_status = Column(String(50))
    promotional_tag = Column(String(200))  # '限時優惠', '滿額免運'
    
    # Metadata
    scraped_at = Column(DateTime, default=datetime.utcnow)
    scrape_session_id = Column(String(100))  # Group prices from same scrape run
    
    # Relationships
    product = relationship("Product", back_populates="price_histories")
    platform = relationship("Platform", back_populates="price_histories")
    
    # Indexes
    __table_args__ = (
        Index('idx_product_date', 'product_id', 'scraped_at'),
        Index('idx_platform_date', 'platform_id', 'scraped_at'),
        Index('idx_scrape_session', 'scrape_session_id'),
    )

class ProductMatch(Base):
    """Link similar products across platforms for comparison"""
    __tablename__ = 'product_matches'
    
    id = Column(Integer, primary_key=True)
    product_a_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_b_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Matching confidence
    similarity_score = Column(Float, nullable=False)  # 0-1 confidence
    match_type = Column(String(50))  # 'exact', 'similar', 'variant'
    match_algorithm = Column(String(100))  # 'name_similarity', 'brand_model_match'
    
    # Status
    is_verified = Column(Boolean, default=False)  # Human-verified match
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product_a = relationship("Product", foreign_keys=[product_a_id])
    product_b = relationship("Product", foreign_keys=[product_b_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_product_match', 'product_a_id', 'product_b_id'),
        Index('idx_similarity_score', 'similarity_score'),
    )

class ScrapeSession(Base):
    """Track scraping sessions for monitoring"""
    __tablename__ = 'scrape_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False)
    
    # Session info
    query = Column(String(200))
    platforms_scraped = Column(String(200))  # JSON list of platforms
    products_found = Column(Integer, default=0)
    success_rate = Column(Float)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Status
    status = Column(String(50), default='running')  # 'running', 'completed', 'failed'
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)