"""PChome scraper - Taiwan's largest e-commerce platform"""
from .base_spider import BaseSpider
from typing import Dict, List, Optional
import re
import json

class PChomeSpider(BaseSpider):
    """Scraper for PChome Online Shopping"""
    
    def __init__(self):
        super().__init__(use_selenium=False)  # PChome works with requests
        self.base_url = "https://24h.pchome.com.tw"
        self.search_url = "https://ecshweb.pchome.com.tw/search/v3.3/all/results"
    
    def search_products(self, query: str, max_pages: int = 3) -> List[Dict]:
        """Search products on PChome"""
        products = []
        
        for page in range(1, max_pages + 1):
            params = {
                'q': query,
                'page': page,
                'sort': 'rnk/dc'  # Sort by relevance
            }
            
            try:
                response = self.session.get(self.search_url, params=params)
                data = response.json()
                
                if 'prods' in data:
                    for item in data['prods']:
                        product = self._parse_search_result(item)
                        if product:
                            products.append(product)
                
                # Check if there are more pages
                if len(data.get('prods', [])) < 20:  # Less than full page
                    break
                    
            except Exception as e:
                print(f"Error searching page {page}: {e}")
                break
        
        return products
    
    def _parse_search_result(self, item: Dict) -> Optional[Dict]:
        """Parse individual search result"""
        try:
            return {
                'platform': 'pchome',
                'product_id': item.get('Id'),
                'name': item.get('name', ''),
                'price': float(item.get('price', 0)),
                'original_price': float(item.get('originPrice', 0)),
                'url': f"https://24h.pchome.com.tw/prod/{item.get('Id')}",
                'image_url': item.get('picB', ''),
                'brand': item.get('brand', ''),
                'description': item.get('describe', ''),
                'availability': item.get('buttonType') == 'buy',
                'scraped_at': None  # Will be set by ETL
            }
        except Exception as e:
            print(f"Error parsing product: {e}")
            return None
    
    def extract_product_info(self, soup, url: str) -> Dict:
        """Extract detailed product info from product page"""
        try:
            # Extract product ID from URL
            product_id_match = re.search(r'/prod/([A-Z0-9-]+)', url)
            product_id = product_id_match.group(1) if product_id_match else ''
            
            # Find product name
            name_elem = soup.find('h1', class_='prod-name') or soup.find('h1')
            name = name_elem.get_text(strip=True) if name_elem else ''
            
            # Find price
            price_elem = soup.find('span', class_='value') or soup.find(class_='price')
            price_text = price_elem.get_text(strip=True) if price_elem else '0'
            price = float(re.sub(r'[^\d.]', '', price_text) or 0)
            
                        # Find images - proper BeautifulSoup element handling
            img_elem = soup.find('img', class_='prod-img')
            image_url = ''
            if img_elem:
                from bs4 import Tag
                if isinstance(img_elem, Tag):
                    image_url = img_elem.get('src', '') or ''
            
            return {
                'platform': 'pchome',
                'product_id': product_id,
                'name': name,
                'price': price,
                'url': url,
                'image_url': image_url,
                'availability': 'add-cart' in str(soup),
                'scraped_at': None
            }
            
        except Exception as e:
            print(f"Error extracting product info: {e}")
            return {
                'platform': 'pchome',
                'product_id': '',
                'name': '',
                'price': 0.0,
                'url': url,
                'image_url': '',
                'availability': False,
                'scraped_at': None
            }