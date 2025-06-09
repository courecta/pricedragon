# Fix the entire pipeline.py file with proper SQLAlchemy handling:

"""
ETL Pipeline: Transform scraper output into clean database records
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
import re
from difflib import SequenceMatcher

from database.connection import get_db
from database.models import Product, Platform, Category, PriceHistory, ScrapeSession, ProductMatch

class ProductETL:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.platform_cache = {}
        self.category_cache = {}
    
    def process_scraper_results(self, scraper_results: List[Dict], query: str = "") -> Dict:
        """
        Main ETL entry point
        Transform scraper results into database records
        """
        print(f"🔄 Starting ETL pipeline for {len(scraper_results)} products")
        
        db = next(get_db())
        
        try:
            # Create scrape session
            session = self._create_scrape_session(db, query, scraper_results)
            
            # Cache platforms and categories
            self._build_caches(db)
            
            # Process each product
            processed_products = []
            for raw_product in scraper_results:
                try:
                    product = self._process_single_product(db, raw_product)
                    if product:
                        processed_products.append(product)
                except Exception as e:
                    print(f"⚠️ Error processing product {raw_product.get('name', 'Unknown')}: {e}")
                    continue
            
            # Find product matches across platforms
            self._find_product_matches(db, processed_products)
            
            # Update session with results - FIX: Use setattr or direct assignment to instances
            session.products_found = len(processed_products)
            session.completed_at = datetime.now(timezone.utc)
            session.status = 'completed'
            session.success_rate = len(processed_products) / len(scraper_results) if scraper_results else 0.0
            
            db.commit()
            
            result = {
                'session_id': self.session_id,
                'products_processed': len(processed_products),
                'success_rate': session.success_rate,
                'products': processed_products
            }
            
            print(f"✅ ETL pipeline completed: {len(processed_products)} products processed")
            return result
            
        except Exception as e:
            print(f"❌ ETL pipeline failed: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def _create_scrape_session(self, db: Session, query: str, results: List[Dict]) -> ScrapeSession:
        """Create tracking record for this scrape session"""
        platforms = list(set(item.get('platform', 'unknown') for item in results))
        
        session = ScrapeSession(
            session_id=self.session_id,
            query=query,
            platforms_scraped=str(platforms),
            started_at=datetime.now(timezone.utc),  # FIX: Use timezone.utc consistently
            status='running'
        )
        
        db.add(session)
        db.flush()  # Get the ID
        return session
    
    def _build_caches(self, db: Session):
        """Cache platforms and categories for fast lookup"""
        # Platform cache
        platforms = db.query(Platform).all()
        self.platform_cache = {p.name: p for p in platforms}
        
        # Category cache  
        categories = db.query(Category).all()
        self.category_cache = {c.name: c for c in categories}
    
    def _process_single_product(self, db: Session, raw_product: Dict) -> Optional[Product]:
        """Transform single raw product into database record"""
        
        # Extract and clean basic info
        name = self._clean_text(raw_product.get('name', ''))
        if not name or len(name) < 3:
            return None
        
        normalized_name = self._normalize_name(name)
        platform_name = raw_product.get('platform', '').lower()
        
        # Get platform
        platform = self.platform_cache.get(platform_name)
        if not platform:
            print(f"⚠️ Unknown platform: {platform_name}")
            return None
        
        # Determine category
        category = self._categorize_product(name)
        
        # Extract pricing
        price_data = self._extract_pricing(raw_product)
        
        # Extract brand and model
        brand, model = self._extract_brand_model(name)
        
        # Check if product already exists
        existing = db.query(Product).filter(
            Product.platform_id == platform.id,
            Product.platform_product_id == raw_product.get('product_id', ''),
        ).first()
        
        if existing:
            # Update existing product - FIX: Direct assignment works for instances
            existing.name = name
            existing.normalized_name = normalized_name
            existing.current_price = price_data['current_price']
            existing.original_price = price_data['original_price']
            existing.discount_percentage = price_data['discount']
            existing.is_available = raw_product.get('availability', True)
            existing.url = raw_product.get('url', '')
            existing.image_url = raw_product.get('image_url', '')
            existing.last_scraped = datetime.now(timezone.utc)
            existing.scrape_count = (existing.scrape_count or 0) + 1  # FIX: Handle None case
            
            product = existing
        else:
            # Create new product
            product = Product(
                name=name,
                normalized_name=normalized_name,
                description=raw_product.get('description', ''),
                brand=brand,
                model=model,
                platform_id=platform.id,
                platform_product_id=raw_product.get('product_id', ''),
                url=raw_product.get('url', ''),
                image_url=raw_product.get('image_url', ''),
                category_id=category.id if category else None,
                current_price=price_data['current_price'],
                original_price=price_data['original_price'],
                discount_percentage=price_data['discount'],
                is_available=raw_product.get('availability', True),
                data_quality_score=self._calculate_quality_score(raw_product),
                last_scraped=datetime.now(timezone.utc)
            )
            
            db.add(product)
            db.flush()  # Get the ID
        
        # Add price history record
        price_history = PriceHistory(
            product_id=product.id,
            platform_id=platform.id,
            price=price_data['current_price'],
            original_price=price_data['original_price'],
            discount_percentage=price_data['discount'],
            availability=raw_product.get('availability', True),
            scraped_at=datetime.now(timezone.utc),
            scrape_session_id=self.session_id
        )
        
        db.add(price_history)
        
        return product
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', str(text)).strip()
        
        # Remove special characters but keep Chinese, English, numbers
        text = re.sub(r'[^\w\s\u4e00-\u9fff\-\(\)\[\]\/]', '', text)
        
        return text[:500]  # Limit length
    
    def _normalize_name(self, name: str) -> str:
        """Create normalized version for matching"""
        normalized = name.lower()
        
        # Remove common noise words
        noise_words = ['的', '【', '】', '(', ')', '[', ']', '限時', '特價', '優惠']
        for word in noise_words:
            normalized = normalized.replace(word, ' ')
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _categorize_product(self, name: str) -> Optional[Category]:
        """Determine product category from name"""
        name_lower = name.lower()
        
        # Category keywords mapping
        category_keywords = {
            'Electronics': ['筆電', '電腦', '手機', 'iphone', 'ipad', '平板', '耳機', '相機', '螢幕'],
            'Fashion': ['運動鞋', '鞋', '包包', '手錶', '衣服', '褲子', '牛仔褲', '外套'],
            'Home': ['咖啡機', '吸塵器', '床墊', '餐具', '廚具', '家具', '燈具'],
            'Gaming': ['switch', 'ps5', 'xbox', '遊戲', '手把', '鍵盤', '滑鼠'],
            'Beauty': ['面膜', '防曬', '口紅', '香水', '化妝', '保養', '護膚'],
            'Sports': ['瑜珈', '啞鈴', '跑鞋', '籃球', '運動', '健身'],
            'Books': ['小說', '食譜', '書', '漫畫', '雜誌'],
            'Food': ['零食', '茶葉', '蜂蜜', '堅果', '咖啡', '茶']
        }
        
        for category_name, keywords in category_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return self.category_cache.get(category_name)  # FIX: This is fine for regular dict
        
        return None
    
    def _extract_pricing(self, raw_product: Dict) -> Dict:
        """Extract and validate pricing information"""
        current_price = float(raw_product.get('price', 0))
        original_price = float(raw_product.get('original_price', current_price))
        
        # Calculate discount
        discount = 0.0
        if original_price > current_price and original_price > 0:
            discount = ((original_price - current_price) / original_price) * 100
        
        return {
            'current_price': current_price,
            'original_price': original_price,
            'discount': discount
        }
    
    def _extract_brand_model(self, name: str) -> Tuple[str, str]:
        """Extract brand and model from product name"""
        name_upper = name.upper()
        
        # Common brands
        brands = ['APPLE', 'SAMSUNG', 'ASUS', 'ACER', 'MSI', 'LENOVO', 'HP', 'DELL', 'SONY', 'LG', 'NIKE', 'ADIDAS']
        
        brand = ""
        for b in brands:
            if b in name_upper:
                brand = b.title()
                break
        
        # Extract model (simplified - could be more sophisticated)
        model = ""
        if 'iPhone' in name:
            model_match = re.search(r'iPhone\s*(\d+\s*\w*)', name, re.IGNORECASE)
            if model_match:
                model = model_match.group(1).strip()
        
        return brand, model
    
    def _calculate_quality_score(self, raw_product: Dict) -> float:
        """Calculate data quality score (0-1)"""
        score = 0.0
        total_checks = 6
        
        # Check for required fields
        if raw_product.get('name') and len(raw_product['name']) > 5:
            score += 1/total_checks
        
        if raw_product.get('price', 0) > 0:
            score += 1/total_checks
        
        if raw_product.get('url'):
            score += 1/total_checks
        
        if raw_product.get('image_url'):
            score += 1/total_checks
        
        if raw_product.get('brand'):
            score += 1/total_checks
        
        if raw_product.get('description'):
            score += 1/total_checks
        
        return round(score, 2)
    
    def _find_product_matches(self, db: Session, products: List[Product]):
        """Find similar products across platforms for comparison"""
        print(f"🔗 Finding product matches across platforms...")
        
        matches_found = 0
        
        for i, product_a in enumerate(products):
            for product_b in products[i+1:]:
                # Skip same platform - FIX: Compare actual values, not Column objects
                if product_a.platform_id == product_b.platform_id:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(product_a, product_b)
                
                if similarity >= 0.7:  # High similarity threshold
                    # Check if match already exists
                    existing_match = db.query(ProductMatch).filter(
                        ((ProductMatch.product_a_id == product_a.id) & (ProductMatch.product_b_id == product_b.id)) |
                        ((ProductMatch.product_a_id == product_b.id) & (ProductMatch.product_b_id == product_a.id))
                    ).first()
                    
                    if not existing_match:
                        match = ProductMatch(
                            product_a_id=product_a.id,
                            product_b_id=product_b.id,
                            similarity_score=similarity,
                            match_type='similar' if similarity < 0.9 else 'exact',
                            match_algorithm='name_similarity'
                        )
                        
                        db.add(match)
                        matches_found += 1
        
        print(f"✅ Found {matches_found} product matches")
    
    def _calculate_similarity(self, product_a: Product, product_b: Product) -> float:
        """Calculate similarity score between two products"""
        # FIX: Access actual string values, not Column objects
        name_a = product_a.normalized_name or ""
        name_b = product_b.normalized_name or ""
        
        # Name similarity (primary factor)
        name_sim = SequenceMatcher(None, name_a, name_b).ratio()
        
        # Brand similarity boost
        brand_sim = 0.0
        brand_a = product_a.brand
        brand_b = product_b.brand
        if brand_a and brand_b:
            if brand_a.lower() == brand_b.lower():
                brand_sim = 0.3
        
        # Price similarity (products shouldn't be too different in price)
        price_sim = 0.0
        price_a = product_a.current_price
        price_b = product_b.current_price
        if price_a and price_b:
            price_diff = abs(float(price_a) - float(price_b))
            max_price = max(float(price_a), float(price_b))
            if max_price > 0:
                price_ratio = 1 - (price_diff / max_price)
                if price_ratio > 0.7:  # Prices within 30% of each other
                    price_sim = 0.1
        
        total_similarity = name_sim + brand_sim + price_sim
        return min(total_similarity, 1.0)
    
    def run_pipeline(self, query: str, enable_matching: bool = True) -> Dict:
        """
        Run the complete ETL pipeline for a search query
        Compatible method for ETLAutomation
        """
        try:
            # Import scrapers
            from scraper.momo_spider import MomoSpider
            from scraper.pchome_spider import PChomeSpider
            from scraper.yahoo_spider import YahooSpider
            
            # Run scrapers
            scrapers = [MomoSpider(), PChomeSpider(), YahooSpider()]
            all_results = []
            
            for scraper in scrapers:
                try:
                    results = scraper.search(query, max_pages=2)
                    all_results.extend(results)
                except Exception as e:
                    print(f"Warning: Scraper {scraper.__class__.__name__} failed: {e}")
                    continue
            
            if not all_results:
                return {
                    'success': False,
                    'error': 'No products found',
                    'products_loaded': 0,
                    'matches_found': 0
                }
            
            # Process results through ETL pipeline
            result = self.process_scraper_results(all_results, query)
            
            return {
                'success': True,
                'products_loaded': result.get('products_processed', 0),
                'matches_found': result.get('matches_created', 0),
                'query': query,
                'total_scraped': len(all_results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'products_loaded': 0,
                'matches_found': 0
            }