"""Test database functionality"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Product, PriceHistory, Base
from database.db_utils import DatabaseManager
from datetime import datetime, timezone

def test_database_connection():
    """Test basic database connection and table creation"""
    print("🔧 Testing database connection...")
    
    try:
        db = DatabaseManager()
        print("✅ Database connection successful")
        print(f"✅ Tables created in: {db.engine.url}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_product_crud():
    """Test Product CRUD operations"""
    print("🔧 Testing Product CRUD operations...")
    
    try:
        db = DatabaseManager()
        session = db.get_session()
        
        # Create a test product
        test_product = Product(
            platform='test',
            product_id='TEST123',
            name='Test iPhone',
            price=999.99,
            url='https://test.com/product/123',
            availability=True
        )
        
        session.add(test_product)
        session.commit()
        
        # Read the product back
        retrieved = session.query(Product).filter_by(product_id='TEST123').first()
        
        success = False
        if retrieved:
            try:
                product_name = str(retrieved.name)
                if product_name == 'Test iPhone':
                    success = True
                    print("✅ Product CRUD test passed")
                else:
                    print(f"❌ Product CRUD test failed - name mismatch: '{product_name}'")
            except AttributeError:
                print("❌ Product CRUD test failed - retrieved object has no name attribute")
        else:
            print("❌ Product CRUD test failed - no product found")
            
        if retrieved:
            session.delete(retrieved)
            session.commit()

        return success
        
    except Exception as e:
        print(f"❌ Product CRUD test failed: {e}")
        return False
    finally:
        if session:
            session.close()

def test_sample_data_insertion():
    """Test inserting sample data using our DatabaseManager"""
    print("🔧 Testing sample data insertion...")
    
    sample_products = [
        {
            'platform': 'pchome',
            'product_id': 'SAMPLE001',
            'name': 'Sample iPhone 15',
            'price': 25000.0,
            'url': 'https://sample.com/iphone15',
            'availability': True,
            'scraped_at': datetime.now(timezone.utc)
        },
        {
            'platform': 'momo',
            'product_id': 'SAMPLE002', 
            'name': 'Sample MacBook Air',
            'price': 35000.0,
            'url': 'https://sample.com/macbook',
            'availability': True,
            'scraped_at': datetime.now(timezone.utc)
        }
    ]
    
    try:
        db = DatabaseManager()
        saved_count = db.save_products(sample_products)
        
        if saved_count == 2:
            print(f"✅ Successfully saved {saved_count} sample products")
            
            # Test search functionality
            results = db.search_products('iPhone')
            print(f"✅ Search test: Found {len(results)} products matching 'iPhone'")
            
            # Test price history
            history = db.get_price_history('pchome', 'SAMPLE001')
            print(f"✅ Price history test: Found {len(history)} price records")
            
            return True
        else:
            print(f"❌ Expected to save 2 products, but saved {saved_count}")
            return False
            
    except Exception as e:
        print(f"❌ Sample data insertion failed: {e}")
        return False

def test_database_queries():
    """Test various database queries"""
    print("🔧 Testing database queries...")
    
    try:
        db = DatabaseManager()
        session = db.get_session()
        
        # Count total products
        total_products = session.query(Product).count()
        print(f"📊 Total products in database: {total_products}")
        
        # Test search queries
        if total_products > 0:
            # Get cheapest products
            cheapest = session.query(Product).order_by(Product.price.asc()).limit(3).all()
            print(f"💰 Cheapest products:")
            for product in cheapest:
                print(f"  - {product.name[:30]}... NT${product.price}")
            
            # Get products by platform
            platforms = session.query(Product.platform).distinct().all()
            print(f"🏪 Available platforms: {[p[0] for p in platforms]}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Database queries failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("🧹 Cleaning up test data...")
    
    try:
        db = DatabaseManager()
        session = db.get_session()
        
        # Remove test products
        test_products = session.query(Product).filter(
            Product.product_id.in_(['TEST123', 'SAMPLE001', 'SAMPLE002'])
        ).all()
        
        for product in test_products:
            session.delete(product)
        
        # Remove test price history
        test_history = session.query(PriceHistory).filter(
            PriceHistory.product_id.in_(['TEST123', 'SAMPLE001', 'SAMPLE002'])
        ).all()
        
        for history in test_history:
            session.delete(history)
        
        session.commit()
        session.close()
        
        print("✅ Test data cleaned up")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Database Layer...")
    print("=" * 50)
    
    # Run tests
    tests = [
        test_database_connection,
        test_product_crud,
        test_sample_data_insertion,
        test_database_queries
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print("-" * 30)
    
    # Cleanup
    cleanup_test_data()
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All database tests passed!")
    else:
        print("⚠️  Some database tests failed")