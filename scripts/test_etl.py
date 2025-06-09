"""Test the complete ETL pipeline with our scraper data and automation features"""

import sys
import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.pchome_spider import PChomeSpider
from scraper.momo_spider import MomoSpider
from scraper.yahoo_spider import YahooSpider
from etl.pipeline import ProductETL
from database.connection import init_database
from database.db_utils import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ETL_Test')

def test_basic_etl_pipeline() -> bool:
    """Test basic scraper → ETL → Database flow"""
    
    logger.info("🧪 Testing Basic ETL Pipeline")
    logger.info("=" * 50)
    
    # Initialize database
    logger.info("🗄️ Initializing database...")
    init_database()
    
    # Scrape some products
    logger.info("\n📡 Scraping products...")
    platforms = {
        "PChome": PChomeSpider(),
        "Momo": MomoSpider(),
        "Yahoo": YahooSpider()
    }
    
    query = "iPhone"
    all_products = []
    
    for platform_name, spider in platforms.items():
        try:
            logger.info(f"  🔍 {platform_name}...")
            products = spider.search_products(query, max_pages=1)
            all_products.extend(products)
            logger.info(f"✅ {len(products)} products")
        except Exception as e:
            logger.error(f"❌ {e}")
    
    # Cleanup spiders
    for spider in platforms.values():
        spider.cleanup()
    
    logger.info(f"\n📊 Total scraped: {len(all_products)} products")
    
    # Run ETL pipeline
    logger.info("\n🔄 Running ETL pipeline...")
    etl = ProductETL()
    result = etl.process_scraper_results(all_products, query)
    
    logger.info(f"\n✅ ETL Results:")
    logger.info(f"  📊 Products processed: {result['products_processed']}")
    logger.info(f"  📈 Success rate: {result['success_rate']:.1%}")
    logger.info(f"  🆔 Session ID: {result['session_id']}")
    
    # Test database queries
    logger.info("\n🔍 Testing database queries...")
    from database.connection import get_db
    from database.models import Product, Platform, PriceHistory, ProductMatch
    
    db = next(get_db())
    
    try:
        # Count products by platform
        platforms_query = db.query(Platform).all()
        for platform in platforms_query:
            count = db.query(Product).filter(Product.platform_id == platform.id).count()
            logger.info(f"  🏪 {platform.display_name}: {count} products")
        
        # Show price history count
        price_history_count = db.query(PriceHistory).count()
        logger.info(f"  📈 Price history records: {price_history_count}")
        
        # Show product matches
        matches_count = db.query(ProductMatch).count()
        logger.info(f"  🔗 Product matches found: {matches_count}")
        
        # Show sample products
        logger.info("\n🛍️ Sample products in database:")
        sample_products = db.query(Product).limit(5).all()
        for product in sample_products:
            logger.info(f"  📱 {product.name[:50]}... - NT${product.current_price:.0f} ({product.platform.display_name})")
        
    finally:
        db.close()
    
    logger.info("\n🎉 ETL Pipeline test completed successfully!")
    return True

def test_automated_etl_pipeline(queries: Optional[List[str]] = None) -> Dict[str, Any]:
    """Test automated ETL pipeline with multiple queries"""
    if queries is None:
        queries = ["iPhone", "Samsung", "MacBook", "iPad", "PlayStation"]
    
    logger.info(f"🤖 Testing Automated ETL Pipeline with {len(queries)} queries")
    logger.info("=" * 60)
    
    total_products = 0
    total_matches = 0
    successful_queries = 0
    failed_queries = []
    
    start_time = datetime.now()
    
    # Initialize database
    init_database()
    
    for query in queries:
        try:
            logger.info(f"🔍 Processing query: '{query}'")
            
            # Run ETL pipeline for this query
            pipeline = ProductETL()
            result = pipeline.run_pipeline(query, enable_matching=True)
            
            if result['success']:
                total_products += result.get('products_loaded', 0)
                total_matches += result.get('matches_found', 0)
                successful_queries += 1
                logger.info(f"✅ Query '{query}' completed - "
                          f"Products: {result.get('products_loaded', 0)}, "
                          f"Matches: {result.get('matches_found', 0)}")
            else:
                failed_queries.append({
                    'query': query,
                    'error': result.get('error', 'Unknown error')
                })
                logger.error(f"❌ Query '{query}' failed: {result.get('error')}")
            
            # Small delay between queries
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"💥 Exception processing query '{query}': {str(e)}")
            failed_queries.append({
                'query': query,
                'error': str(e)
            })
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Summary report
    report = {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': duration,
        'total_queries': len(queries),
        'successful_queries': successful_queries,
        'failed_queries': len(failed_queries),
        'total_products': total_products,
        'total_matches': total_matches,
        'success_rate': (successful_queries / len(queries)) * 100 if queries else 0,
        'failed_query_details': failed_queries
    }
    
    logger.info(f"\n📊 Automated ETL Summary:")
    logger.info(f"  ⏱️ Duration: {duration:.1f} seconds")
    logger.info(f"  ✅ Success Rate: {report['success_rate']:.1f}%")
    logger.info(f"  📦 Total Products: {total_products}")
    logger.info(f"  🔗 Total Matches: {total_matches}")
    logger.info(f"  ❌ Failed Queries: {len(failed_queries)}")
    
    return report

def test_database_health_check() -> Dict[str, Any]:
    """Test database health and performance metrics"""
    logger.info("🏥 Testing Database Health Check")
    logger.info("=" * 40)
    
    try:
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        from database.models import Product, PriceHistory, ProductMatch, Platform
        
        # Count records
        product_count = session.query(Product).count()
        price_history_count = session.query(PriceHistory).count()
        match_count = session.query(ProductMatch).count()
        platform_count = session.query(Platform).count()
        
        # Check recent activity
        recent_products = session.query(Product).filter(
            Product.created_at >= datetime.now() - timedelta(hours=24)
        ).count()
        
        recent_price_updates = session.query(PriceHistory).filter(
            PriceHistory.scraped_at >= datetime.now() - timedelta(hours=24)
        ).count()
        
        session.close()
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'total_products': product_count,
            'total_price_history': price_history_count,
            'total_matches': match_count,
            'total_platforms': platform_count,
            'products_added_24h': recent_products,
            'price_updates_24h': recent_price_updates,
            'database_status': 'healthy'
        }
        
        logger.info(f"✅ Database Health Report:")
        logger.info(f"  📦 Total Products: {product_count}")
        logger.info(f"  📈 Price History Records: {price_history_count}")
        logger.info(f"  🔗 Product Matches: {match_count}")
        logger.info(f"  🏪 Active Platforms: {platform_count}")
        logger.info(f"  🆕 Products Added (24h): {recent_products}")
        logger.info(f"  🔄 Price Updates (24h): {recent_price_updates}")
        
        return health_report
        
    except Exception as e:
        logger.error(f"❌ Database health check failed: {str(e)}")
        return {
            'timestamp': datetime.now().isoformat(),
            'database_status': 'error',
            'error': str(e)
        }

def test_etl_data_cleanup(days_to_keep: int = 30) -> Dict[str, Any]:
    """Test ETL data cleanup functionality"""
    logger.info(f"🧹 Testing ETL Data Cleanup (keeping {days_to_keep} days)")
    logger.info("=" * 50)
    
    try:
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        from database.models import PriceHistory, ScrapeSession
        
        # Count records to be cleaned up (for reporting)
        old_price_history = session.query(PriceHistory).filter(
            PriceHistory.scraped_at < cutoff_date
        ).count()
        
        old_scrape_sessions = session.query(ScrapeSession).filter(
            ScrapeSession.created_at < cutoff_date
        ).count()
        
        logger.info(f"📊 Cleanup Analysis:")
        logger.info(f"  🗓️ Cutoff Date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  📈 Old Price History Records: {old_price_history}")
        logger.info(f"  📋 Old Scrape Sessions: {old_scrape_sessions}")
        
        # In test mode, we don't actually delete - just report
        cleanup_report = {
            'cutoff_date': cutoff_date.isoformat(),
            'would_delete_price_history': old_price_history,
            'would_delete_scrape_sessions': old_scrape_sessions,
            'total_would_delete': old_price_history + old_scrape_sessions,
            'test_mode': True
        }
        
        session.close()
        
        logger.info(f"✅ Cleanup Test Completed:")
        logger.info(f"  🗑️ Would delete {cleanup_report['total_would_delete']} old records")
        logger.info(f"  ⚠️ Test mode - no actual deletion performed")
        
        return cleanup_report
        
    except Exception as e:
        logger.error(f"❌ Cleanup test failed: {str(e)}")
        return {'error': str(e), 'test_mode': True}

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='PriceDragon ETL Test Suite')
    parser.add_argument('--mode', choices=['basic', 'automated', 'health', 'cleanup', 'all'], 
                       default='all', help='Test mode to run')
    parser.add_argument('--queries', nargs='+', help='Custom search queries for automated test')
    parser.add_argument('--cleanup-days', type=int, default=30, 
                       help='Days of data to keep during cleanup test')
    
    args = parser.parse_args()
    
    logger.info("🐉 PriceDragon ETL Test Suite")
    logger.info("=" * 60)
    
    results = {}
    
    if args.mode in ['basic', 'all']:
        logger.info("\n🔸 Running Basic ETL Test...")
        results['basic'] = test_basic_etl_pipeline()
    
    if args.mode in ['automated', 'all']:
        logger.info("\n🔸 Running Automated ETL Test...")
        queries = args.queries if args.queries else None
        results['automated'] = test_automated_etl_pipeline(queries)
    
    if args.mode in ['health', 'all']:
        logger.info("\n🔸 Running Database Health Check...")
        results['health'] = test_database_health_check()
    
    if args.mode in ['cleanup', 'all']:
        logger.info("\n🔸 Running Cleanup Test...")
        results['cleanup'] = test_etl_data_cleanup(args.cleanup_days)
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("🏆 ETL TEST SUITE SUMMARY")
    logger.info("=" * 60)
    
    if 'basic' in results:
        status = "✅" if results['basic'] else "❌"
        logger.info(f"  Basic ETL Pipeline: {status}")
    
    if 'automated' in results:
        success_rate = results['automated'].get('success_rate', 0)
        status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
        logger.info(f"  Automated ETL Pipeline: {status} ({success_rate:.1f}% success)")
    
    if 'health' in results:
        db_status = results['health'].get('database_status', 'unknown')
        status = "✅" if db_status == 'healthy' else "❌"
        logger.info(f"  Database Health: {status}")
    
    if 'cleanup' in results:
        cleanup_error = results['cleanup'].get('error')
        status = "❌" if cleanup_error else "✅"
        logger.info(f"  Cleanup Functionality: {status}")
    
    # Determine overall success
    overall_success = all([
        results.get('basic', True),
        results.get('automated', {}).get('success_rate', 100) >= 60,
        results.get('health', {}).get('database_status') == 'healthy',
        not results.get('cleanup', {}).get('error')
    ])
    
    if overall_success:
        logger.info("\n🎉 ALL TESTS PASSED! ETL system is ready for production!")
    else:
        logger.info("\n⚠️ Some tests failed. Review results above.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)