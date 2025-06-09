"""Momo Shopping scraper"""
from .base_spider import BaseSpider
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
import logging

class MomoSpider(BaseSpider):
    def __init__(self):
        # Don't use Selenium for now - use regular HTTP requests
        super().__init__(use_selenium=False)
        self.platform = "momo"
        self.base_url = "https://www.momoshop.com.tw"
        self.search_url = "https://m.momoshop.com.tw/search.momo"
    
    def extract_product_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract product information from individual product page"""
        # This method is required by BaseSpider but not used in our search flow
        try:
            name_elem = soup.find('h1') or soup.find('title')
            price_elem = soup.find('span', class_='price') or soup.find('strong')
            
            name = name_elem.get_text(strip=True) if name_elem else "Unknown Product"
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = self._extract_price(price_text)
            
            return {
                'platform': self.platform,
                'product_id': self._generate_product_id(name, url),
                'name': name,
                'price': price,
                'original_price': price,
                'url': url,
                'image_url': '',
                'brand': self._extract_brand(name),
                'description': name,
                'availability': True,
                'category': None
            }
        except Exception:
            return {
                'platform': self.platform,
                'product_id': 'unknown',
                'name': 'Unknown Product',
                'price': 0.0,
                'original_price': 0.0,
                'url': url,
                'image_url': '',
                'brand': '',
                'description': '',
                'availability': False,
                'category': None
            }
    
    # Update the _parse_search_result method in MomoSpider:

    # Update the _parse_search_result method:

    def _parse_search_result(self, item) -> Optional[Dict]:
        """Parse individual product from search results"""
        try:
            # Try to extract product info
            name_elem = item.find('a', title=True)  # The <a> tag has the title with product name

            # Price is likely in a different element - let's look for it
            price_elem = item.find('span', class_='price') or \
                        item.find('b', class_='price') or \
                        item.find('strong') or \
                        item.find('div', class_='priceArea')

            # Extract URL using goodscode attribute
            url_elem = item.find('a', goodscode=True)  # Look for goodscode attribute

            if not name_elem:
                return None

            # Extract data
            name = name_elem.get('title', '') or name_elem.get_text(strip=True)

            # Extract price - might need to look deeper
            price = 0.0
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._extract_price(price_text)

            # Build URL using goodscode
            url = ""
            if url_elem and url_elem.get('goodscode'):
                goodscode = url_elem.get('goodscode')
                # Construct the real product URL
                url = f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={goodscode}"

            # If still no price found, try to find it in the item
            if price <= 0:
                # Look for any element containing NT$ or price patterns
                all_text = item.get_text()
                import re
                price_matches = re.findall(r'NT?\$?[\d,]+', all_text)
                if price_matches:
                    price = self._extract_price(price_matches[0])

            # Skip if essential data is missing
            if not name or not url:
                return None

            return {
                'platform': self.platform,
                'product_id': self._generate_product_id(name, url),
                'name': name[:200],
                'price': price,
                'original_price': price,
                'url': url,  # Now this should be a real URL!
                'image_url': self._extract_image_url(item),
                'brand': self._extract_brand(name),
                'description': name,
                'availability': True,
                'category': None
            }

        except Exception as e:
            print(f"❌ Error parsing Momo product: {e}")
            return None
    
    def search_products(self, query: str, max_pages: int = 3) -> List[Dict]:
        """Search for products on Momo"""
        products = []
        for page in range(1, max_pages + 1):
            try:
                search_url = f"{self.search_url}?searchKeyword={query}&curPage={page}"
                soup = self.get_page(search_url)
                
                # Use the correct selector we discovered!
                product_items = soup.find_all('li', class_='goodsItemLi')
                
                if not product_items:
                    print(f"⚠️ No products found on page {page}")
                    break
                
                print(f"🔍 Found {len(product_items)} raw items on page {page}")
                
                for item in product_items:
                    product = self._parse_search_result(item)
                    if product:
                        products.append(product)
                    if len(products) >= 20:  # Limit to avoid too many results
                        break
                
                # Add delay
                import time
                time.sleep(1)
            
            except Exception as e:
                print(f"❌ Error scraping Momo page {page}: {e}")
                break
        
        print(f"✅ Successfully parsed {len(products)} products from Momo")
        return products
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        try:
            price_str = re.sub(r'[^\d.]', '', price_text)
            return float(price_str) if price_str else 0.0
        except:
            return 0.0
    
    def _extract_image_url(self, item) -> str:
        """Extract product image URL"""
        try:
            img_elem = item.find('img')
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src and src.startswith('http'):
                    return src
        except:
            pass
        return ""
    
    def _extract_brand(self, name: str) -> str:
        """Try to extract brand from product name"""
        brands = ['Apple', 'Samsung', 'ASUS', 'Acer', 'MSI', 'Lenovo', 'HP', 'Dell']
        name_upper = name.upper()
        
        for brand in brands:
            if brand.upper() in name_upper:
                return brand
        
        return ""
    
    def _generate_product_id(self, name: str, url: str) -> str:
        """Generate a unique product ID"""
        import hashlib
        source = url if url else name
        return hashlib.md5(source.encode()).hexdigest()[:12]