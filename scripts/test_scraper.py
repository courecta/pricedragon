#!/usr/bin/env python3
"""
PriceDragon Scraper Test Suite
Comprehensive testing for all web scrapers and integration functionality
"""
import sys
import os
import time
from typing import Dict, List, Any, Tuple

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.pchome_spider import PChomeSpider
from scraper.momo_spider import MomoSpider
from scraper.yahoo_spider import YahooSpider
from etl.pipeline import ProductETL
from database.db_utils import DatabaseManager

def test_yahoo_scraper() -> bool:
    """Test Yahoo scraper functionality"""
    print("🔍 Testing Yahoo scraper...")
    spider = YahooSpider()
    
    try:
        products = spider.search_products("iPhone", max_pages=1)
        print(f"✅ Found {len(products)} products on Yahoo")
        
        if products:
            sample = products[0]
            print(f"📱 Sample: {sample['name'][:50]}... - NT${sample['price']}")
            print(f"🔗 URL: {sample['url'][:60]}...")
        
        return len(products) > 0
    except Exception as e:
        print(f"❌ Yahoo test failed: {e}")
        return False
    finally:
        spider.cleanup()

def test_pchome_scraper() -> bool:
    """Test PChome scraper functionality"""
    print("🔍 Testing PChome scraper...")
    spider = PChomeSpider()
    
    try:
        products = spider.search_products("iPhone", max_pages=1)
        print(f"✅ Found {len(products)} products on PChome")
        
        if products:
            sample = products[0]
            print(f"📱 Sample: {sample['name'][:50]}... - NT${sample['price']}")
        
        return len(products) > 0
    except Exception as e:
        print(f"❌ PChome test failed: {e}")
        return False
    finally:
        spider.cleanup()

def test_momo_scraper() -> bool:
    """Test Momo scraper functionality"""
    print("🔍 Testing Momo scraper...")
    spider = MomoSpider()
    
    try:
        products = spider.search_products("iPhone", max_pages=1)
        print(f"✅ Found {len(products)} products on Momo")
        
        if products:
            sample = products[0]
            print(f"📱 Sample: {sample['name'][:50]}... - NT${sample['price']}")
            print(f"🔗 URL: {sample['url'][:60]}...")
        
        return len(products) > 0
    except Exception as e:
        print(f"❌ Momo test failed: {e}")
        return False
    finally:
        spider.cleanup()

def test_multi_platform_integration() -> bool:
    """Test complete multi-platform integration pipeline"""
    print("\n🧪 Testing Multi-Platform Integration...")
    
    pchome_spider = PChomeSpider()
    momo_spider = MomoSpider()
    
    try:
        print("🔍 Collecting products from all platforms...")
        
        # Collect from PChome
        pchome_products = pchome_spider.search_products("iPhone", max_pages=1)
        print(f"📦 PChome: {len(pchome_products)} products")
        
        # Collect from Momo  
        momo_products = momo_spider.search_products("iPhone", max_pages=1)
        print(f"📦 Momo: {len(momo_products)} products")
        
        # Combine all products
        all_products = pchome_products + momo_products
        print(f"📊 Total products: {len(all_products)}")
        
        if all_products:
            # Test ETL pipeline
            print("🔄 Running ETL pipeline...")
            pipeline = ProductETL()
            result = pipeline.process_scraper_results(all_products, "multi_platform_test")
            
            print(f"""
ETL Results:
  ✅ Success: {result.get('products_processed', 0)}
  📊 Success Rate: {result.get('success_rate', 0.0):.1%}
  🆔 Session: {result.get('session_id', 'N/A')}
            """)
            
            # Test platform filtering
            print("🔍 Testing platform filtering...")
            db = DatabaseManager()
            
            all_iphone = db.search_products("iPhone")
            pchome_iphone = db.search_products("iPhone", platform_filter="pchome")
            momo_iphone = db.search_products("iPhone", platform_filter="momo")
            
            print(f"📱 Total iPhone products: {len(all_iphone)}")
            print(f"🏪 PChome iPhone products: {len(pchome_iphone)}")
            print(f"🛒 Momo iPhone products: {len(momo_iphone)}")
            
            # Success criteria - at least 1 platform should work
            platform_count = sum([
                len(pchome_iphone) > 0,
                len(momo_iphone) > 0,
            ])
            
            success = (
                result.get('success_rate', 0.0) > 0.5 and  # 50%+ success rate
                platform_count >= 1           # At least 1 platform working
            )
            
            return success
        else:
            print("❌ No products collected from any platform")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
    finally:
        pchome_spider.cleanup()
        momo_spider.cleanup()

def test_product_category_diversity() -> Tuple[bool, Dict[str, Any]]:
    """Test scrapers with diverse product categories"""
    print("🧪 Testing Product Category Diversity...")
    print("=" * 60)
    
    # Diverse product categories to test
    test_categories = {
        "Electronics": ["筆電", "耳機", "相機", "平板"],
        "Fashion": ["運動鞋", "牛仔褲", "包包", "手錶"],
        "Home": ["咖啡機", "吸塵器", "床墊", "餐具"],
        "Gaming": ["Switch", "PS5", "遊戲手把", "鍵盤"],
        "Beauty": ["面膜", "防曬乳", "口紅", "香水"],
        "Sports": ["瑜珈墊", "啞鈴", "跑鞋", "籃球"],
    }
    
    platforms = {
        "PChome": PChomeSpider(),
        "Momo": MomoSpider(),
        "Yahoo": YahooSpider()
    }
    
    total_results = {}
    category_success = {}
    
    try:
        for category, products in test_categories.items():
            print(f"\n🎯 Testing Category: {category}")
            print("-" * 40)
            
            category_results = {}
            
            for product in products:
                print(f"\n🔍 Searching for: {product}")
                product_results = {}
                
                for platform_name, spider in platforms.items():
                    try:
                        print(f"  📡 {platform_name}...", end=" ")
                        
                        # Search with max_pages=1 for speed
                        results = spider.search_products(product, max_pages=1)
                        count = len(results)
                        
                        product_results[platform_name] = {
                            'count': count,
                            'success': count > 0,
                            'samples': results[:2] if results else []  # First 2 samples
                        }
                        
                        status = "✅" if count > 0 else "❌"
                        print(f"{status} {count} products")
                        
                    except Exception as e:
                        product_results[platform_name] = {
                            'count': 0,
                            'success': False,
                            'error': str(e),
                            'samples': []
                        }
                        print(f"❌ Error: {e}")
                    
                    # Add small delay between platforms
                    time.sleep(1)
                
                category_results[product] = product_results
            
            total_results[category] = category_results
            
            # Calculate category success rate
            category_success[category] = calculate_category_success(category_results, list(platforms.keys()))
            
            print(f"\n📊 {category} Summary:")
            for platform in platforms.keys():
                success_count = sum(1 for product_data in category_results.values() 
                                  if product_data[platform]['success'])
                total_count = len(products)
                success_rate = (success_count / total_count) * 100
                print(f"  {platform}: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        # Final comprehensive analysis
        overall_success = print_diversity_analysis(total_results, category_success, list(platforms.keys()))
        
        return overall_success, total_results
        
    finally:
        for spider in platforms.values():
            spider.cleanup()

def calculate_category_success(category_results: Dict[str, Any], platforms: List[str]) -> Dict[str, Tuple[int, int, float]]:
    """Calculate success metrics for a category"""
    platform_success = {}
    
    for platform in platforms:
        successes = sum(1 for product_data in category_results.values() 
                       if product_data[platform]['success'])
        total = len(category_results)
        platform_success[platform] = (successes, total, successes/total if total > 0 else 0)
    
    return platform_success

def print_diversity_analysis(total_results: Dict[str, Any], category_success: Dict[str, Any], platforms: List[str]) -> bool:
    """Print detailed analysis of diversity test results"""
    print("\n" + "=" * 60)
    print("🏆 DIVERSITY TEST ANALYSIS")
    print("=" * 60)
    
    # Overall platform performance
    print("\n📊 Platform Performance Across All Categories:")
    platform_totals = {platform: {'success': 0, 'total': 0} for platform in platforms}
    
    for category_data in category_success.values():
        for platform in platforms:
            success, total, rate = category_data[platform]
            platform_totals[platform]['success'] += success
            platform_totals[platform]['total'] += total
    
    for platform in platforms:
        success = platform_totals[platform]['success']
        total = platform_totals[platform]['total']
        rate = (success / total * 100) if total > 0 else 0
        print(f"  🏪 {platform}: {success}/{total} products ({rate:.1f}% success rate)")
    
    # Category difficulty analysis
    print("\n🎯 Category Difficulty Ranking:")
    category_avg_success = {}
    
    for category, platform_data in category_success.items():
        total_success = sum(data[0] for data in platform_data.values())
        total_attempts = sum(data[1] for data in platform_data.values()) 
        avg_rate = (total_success / total_attempts * 100) if total_attempts > 0 else 0
        category_avg_success[category] = avg_rate
    
    # Sort by success rate
    sorted_categories = sorted(category_avg_success.items(), key=lambda x: x[1], reverse=True)
    
    for i, (category, rate) in enumerate(sorted_categories, 1):
        difficulty = "🟢 Easy" if rate > 80 else "🟡 Medium" if rate > 60 else "🔴 Hard"
        print(f"  {i}. {category}: {rate:.1f}% - {difficulty}")
    
    # Sample products showcase
    print("\n🛍️ Sample Products Found:")
    sample_count = 0
    
    for category, category_data in total_results.items():
        if sample_count >= 5:  # Limit samples
            break
            
        for product, platform_data in category_data.items():
            for platform, data in platform_data.items():
                if data.get('samples') and sample_count < 5:
                    sample = data['samples'][0]
                    print(f"  📱 {sample['name'][:50]}... - NT${sample['price']:.0f} ({platform})")
                    sample_count += 1
                    break
            if sample_count >= 5:
                break
    
    # Final verdict
    total_success = sum(platform_totals[p]['success'] for p in platforms)
    total_attempts = sum(platform_totals[p]['total'] for p in platforms)
    overall_rate = (total_success / total_attempts * 100) if total_attempts > 0 else 0
    
    print(f"\n🎉 DIVERSITY TEST VERDICT:")
    print(f"   🏆 Overall Success Rate: {overall_rate:.1f}%")
    print(f"   📊 Total Products Found: {total_success}")
    print(f"   🎯 Categories Tested: {len(total_results)}")
    print(f"   🏪 Platforms Working: {len([p for p in platforms if platform_totals[p]['success'] > 0])}/3")
    
    success_threshold = overall_rate >= 60
    if overall_rate >= 75:
        print("   ✅ EXCELLENT - Production ready for diverse categories!")
    elif overall_rate >= 60:
        print("   👍 GOOD - Strong multi-category performance!")
    elif overall_rate >= 40:
        print("   ⚠️ MODERATE - Some categories need attention")
    else:
        print("   🔧 NEEDS WORK - Platform-specific issues detected")
    
    return success_threshold

def main():
    """Run comprehensive scraper test suite"""
    print("🧪 PriceDragon Comprehensive Scraper Test Suite")
    print("=" * 60)
    
    # Test individual platforms
    pchome_ok = test_pchome_scraper()
    print()
    momo_ok = test_momo_scraper()
    print()
    yahoo_ok = test_yahoo_scraper()
    print()
    
    # Test comprehensive features
    diversity_ok, diversity_results = test_product_category_diversity()
    print()
    integration_ok = test_multi_platform_integration()
    print()
    
    print("=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS:")
    print(f"  🏪 PChome Scraper: {'✅' if pchome_ok else '❌'}")
    print(f"  🛒 Momo Scraper: {'✅' if momo_ok else '❌'}")
    print(f"  🛒 Yahoo Scraper: {'✅' if yahoo_ok else '❌'}")
    print(f"  🎯 Category Diversity: {'✅' if diversity_ok else '❌'}")
    print(f"  🔄 Multi-Platform Integration: {'✅' if integration_ok else '❌'}")
    
    # Calculate final score
    platform_success = [pchome_ok, momo_ok, yahoo_ok]
    success_count = sum(platform_success)
    
    print(f"\n🏆 Final Score: {success_count}/3 platforms working")
    
    if success_count == 3 and diversity_ok and integration_ok:
        print("🎉 PERFECT! All systems fully operational!")
    elif success_count >= 2 and (diversity_ok or integration_ok):
        print("✅ EXCELLENT! Multi-platform system ready for production!")
    elif success_count >= 1:
        print("👍 GOOD! Basic functionality working, some improvements needed")
    else:
        print("⚠️ NEEDS WORK! Critical issues require attention")
    
    return success_count >= 2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)