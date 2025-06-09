"""
Database Performance Optimizations
Add indexes and query optimizations for better performance
"""

from sqlalchemy import text
from database.connection import engine
from database.db_utils import DatabaseManager
import logging, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logger = logging.getLogger(__name__)

def create_performance_indexes():
    """Create indexes for better query performance"""
    
    indexes = [
        # Product search indexes
        "CREATE INDEX IF NOT EXISTS idx_products_normalized_name ON products(normalized_name)",
        "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)",
        "CREATE INDEX IF NOT EXISTS idx_products_platform_available ON products(platform_id, is_available)",
        "CREATE INDEX IF NOT EXISTS idx_products_price_range ON products(current_price) WHERE current_price IS NOT NULL",
        
        # Price history indexes
        "CREATE INDEX IF NOT EXISTS idx_price_history_product_date ON price_history(product_id, scraped_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_price_history_platform_date ON price_history(platform_id, scraped_at DESC)",
        
        # Product matches indexes
        "CREATE INDEX IF NOT EXISTS idx_product_matches_similarity ON product_matches(similarity_score DESC)",
        "CREATE INDEX IF NOT EXISTS idx_product_matches_active ON product_matches(is_active, similarity_score DESC)",
        
        # Platform indexes
        "CREATE INDEX IF NOT EXISTS idx_platforms_active ON platforms(is_active)",
        
        # Search optimization indexes
        "CREATE INDEX IF NOT EXISTS idx_products_search_composite ON products(platform_id, is_available, current_price) WHERE current_price IS NOT NULL",
    ]
    
    try:
        with engine.connect() as connection:
            for index_sql in indexes:
                try:
                    connection.execute(text(index_sql))
                    index_name = index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unnamed'
                    logger.info(f"Created index: {index_name}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")
            
            connection.commit()
            logger.info("Database performance optimization completed")
        
    except Exception as e:
        logger.error(f"Failed to optimize database: {e}")
        raise

def optimize_database_settings():
    """Optimize SQLite database settings for better performance"""
    
    settings = [
        "PRAGMA journal_mode = WAL",  # Write-Ahead Logging for better concurrency
        "PRAGMA synchronous = NORMAL",  # Balance between safety and speed
        "PRAGMA cache_size = 10000",  # Increase cache size
        "PRAGMA temp_store = MEMORY",  # Store temporary tables in memory
        "PRAGMA mmap_size = 268435456",  # Enable memory-mapped I/O (256MB)
    ]
    
    try:
        with engine.connect() as connection:
            for setting in settings:
                connection.execute(text(setting))
                logger.info(f"Applied setting: {setting}")
            
            connection.commit()
            logger.info("Database settings optimization completed")
        
    except Exception as e:
        logger.error(f"Failed to optimize database settings: {e}")
        raise

def get_database_stats():
    """Get database performance statistics"""
    
    stats_queries = {
        'total_products': "SELECT COUNT(*) FROM products",
        'available_products': "SELECT COUNT(*) FROM products WHERE is_available = 1",
        'platforms_count': "SELECT COUNT(*) FROM platforms WHERE is_active = 1",
        'price_history_records': "SELECT COUNT(*) FROM price_history",
        'product_matches': "SELECT COUNT(*) FROM product_matches WHERE is_active = 1",
        'avg_price': "SELECT AVG(current_price) FROM products WHERE current_price IS NOT NULL",
    }
    
    try:
        with engine.connect() as connection:
            stats = {}
            
            for stat_name, query in stats_queries.items():
                result = connection.execute(text(query)).fetchone()
                stats[stat_name] = result[0] if result else 0
            
            return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("Starting database performance optimization...")
    
    # Get initial stats
    print("\nInitial database statistics:")
    initial_stats = get_database_stats()
    for key, value in initial_stats.items():
        print(f"  {key}: {value}")
    
    # Apply optimizations
    print("\nOptimizing database settings...")
    optimize_database_settings()
    
    print("\nCreating performance indexes...")
    create_performance_indexes()
    
    # Get final stats
    print("\nFinal database statistics:")
    final_stats = get_database_stats()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    print("\nDatabase optimization completed!")
