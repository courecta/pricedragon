"""Database utilities"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base, Product, PriceHistory, ScrapeSession
import os, logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from database.models import Base, Product, PriceHistory

class DatabaseManager:
    """Database manager for PriceDragon"""
    
    def __init__(self, database_url: Optional[str] = None):
        if not database_url:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///data/pricedragon.db')
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def save_products(self, products: List[Dict]) -> int:
        """Save products to database"""
        session = self.get_session()
        saved_count = 0
        
        try:
            for product_data in products:
                # Check if product already exists
                existing = session.query(Product).filter_by(
                    platform=product_data['platform'],
                    product_id=product_data['product_id']
                ).first()
                
                if existing:
                    # Update existing product
                    for key, value in product_data.items():
                        if key != 'scraped_at':  # Don't update scraped_at
                            setattr(existing, key, value)
                    
                    # Save price history
                    price_history = PriceHistory(
                        platform=product_data['platform'],
                        product_id=product_data['product_id'],
                        price=product_data['price'],
                        availability=product_data['availability'],
                        scraped_at=product_data.get('scraped_at')
                    )
                    session.add(price_history)
                else:
                    # Create new product
                    product = Product(**{k: v for k, v in product_data.items() if k != 'scraped_at'})
                    session.add(product)
                    
                    # Save initial price history
                    price_history = PriceHistory(
                        platform=product_data['platform'],
                        product_id=product_data['product_id'],
                        price=product_data['price'],
                        availability=product_data['availability'],
                        scraped_at=product_data.get('scraped_at')
                    )
                    session.add(price_history)
                
                saved_count += 1
            
            session.commit()
            return saved_count
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def search_products(self, query: str, limit: int = 50, platform_filter: Optional[str] = None) -> List:
        """Search products in database"""
        session = self.get_session()
        
        try:
            # Log search query (simplified)
            print(f"Searching for products: {query}")
            
            # Search products with platform filter
            query_obj = session.query(Product).filter(Product.name.contains(query))
            
            # Apply platform filter if provided
            if platform_filter:
                # Join with Platform table and filter by platform name
                from .models import Platform
                query_obj = query_obj.join(Platform).filter(Platform.name == platform_filter)
            
            products = query_obj.order_by(Product.current_price.asc()).limit(limit).all()
            
            session.commit()
            return products
            
        finally:
            session.close()
    
    def get_price_history(self, platform: str, product_id: str) -> List[PriceHistory]:
        """Get price history for a product"""
        session = self.get_session()
        
        try:
            return session.query(PriceHistory).filter_by(
                platform=platform,
                product_id=product_id
            ).order_by(PriceHistory.scraped_at.asc()).all()
        finally:
            session.close()