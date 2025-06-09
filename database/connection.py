"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator
from .models import Base

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./pricedragon.db')

# Create engine
if DATABASE_URL.startswith('sqlite'):
    # SQLite configuration for development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True  # Set to False in production
    )
else:
    # PostgreSQL/MySQL configuration for production
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    print("🗄️ Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with default data"""
    create_tables()
    
    # Add default platforms
    db = SessionLocal()
    try:
        from .models import Platform, Category
        
        # Check if platforms already exist
        if db.query(Platform).count() == 0:
            print("📊 Adding default platforms...")
            
            platforms = [
                Platform(name='pchome', display_name='PChome線上購物', base_url='https://24h.pchome.com.tw'),
                Platform(name='momo', display_name='momo購物網', base_url='https://www.momoshop.com.tw'),
                Platform(name='yahoo', display_name='Yahoo購物中心', base_url='https://tw.buy.yahoo.com'),
            ]
            
            for platform in platforms:
                db.add(platform)
            
            db.commit()
            print("✅ Default platforms added")
        
        # Check if categories already exist
        if db.query(Category).count() == 0:
            print("📊 Adding default categories...")
            
            categories = [
                Category(name='Electronics', name_zh='電子產品'),
                Category(name='Fashion', name_zh='時尚'),
                Category(name='Home', name_zh='居家'),
                Category(name='Gaming', name_zh='遊戲'),
                Category(name='Beauty', name_zh='美妝'),
                Category(name='Sports', name_zh='運動'),
                Category(name='Books', name_zh='書籍'),
                Category(name='Food', name_zh='食品'),
            ]
            
            for category in categories:
                db.add(category)
            
            db.commit()
            print("✅ Default categories added")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()