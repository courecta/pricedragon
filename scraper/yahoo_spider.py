# Replace with this production-ready version:

"""Yahoo Shopping Taiwan scraper - Production Version"""
from .base_spider import BaseSpider
from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional
import re

class YahooSpider(BaseSpider):
    def __init__(self):
        super().__init__(use_selenium=False)
        self.platform = "yahoo"
        self.base_url = "https://tw.buy.yahoo.com"
        self.search_url = f"{self.base_url}/search/product"
    
    def extract_product_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract product information from individual Yahoo product page"""
        try:
            # For individual product pages
            name_elem = soup.find('h1') or soup.find('title')
            price_elem = soup.find('span', class_='price') or soup.find('em')
            
            name = name_elem.get_text(strip=True) if isinstance(name_elem, Tag) else "Yahoo Product"
            price_text = price_elem.get_text(strip=True) if isinstance(price_elem, Tag) else "0"
            price = self._extract_price(price_text)
            
            return {
                'platform': self.platform,
                'product_id': self._generate_product_id(name, url),
                'name': name[:200],
                'price': price,
                'original_price': price,
                'url': url,
                'image_url': '',
                'brand': self._extract_brand(name),
                'description': name,
                'availability': True,
                'category': None
            }
            
        except Exception as e:
            print(f"❌ Error extracting Yahoo product info: {e}")
            return self._create_empty_product(url)
    
    def search_products(self, query: str, max_pages: int = 3) -> List[Dict]:
        """Search for products on Yahoo Shopping Taiwan"""
        products = []
        
        for page in range(1, max_pages + 1):
            try:
                # Yahoo search URL with pagination
                search_url = f"{self.search_url}?p={query}&page={page}"
                
                soup = self.get_page(search_url)
                
                # Use discovered selectors - prioritize gridItem class
                product_items = self._find_yahoo_products(soup)
                
                if not product_items:
                    print(f"⚠️ No products found on Yahoo page {page}")
                    break
                
                print(f"🔍 Found {len(product_items)} raw items on Yahoo page {page}")
                
                for item in product_items:
                    product = self._parse_yahoo_product(item)
                    if product:
                        products.append(product)
                
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error scraping Yahoo page {page}: {e}")
                break
        
        print(f"✅ Successfully parsed {len(products)} products from Yahoo")
        return products
    
    def _find_yahoo_products(self, soup: BeautifulSoup) -> List[Tag]:
        """Find Yahoo product containers using discovered patterns"""
        # Strategy 1: Look for gridItem class (discovered pattern)
        grid_items = soup.find_all('div', class_='gridItem')
        if grid_items:
            tag_items = [item for item in grid_items if isinstance(item, Tag)]
            print(f"✅ Found {len(grid_items)} products using gridItem class")
            return tag_items
        
        # Strategy 2: Look for other item-related classes
        item_selectors = [
            ('div', 'productItem'),
            ('li', 'item'),
            ('div', 'product-item'),
            ('article', 'product'),
        ]
        
        for tag, class_name in item_selectors:
            elements = soup.find_all(tag, class_=class_name)
            if elements:
                tag_elements = [elem for elem in elements if isinstance(elem, Tag)]
                print(f"✅ Found {len(elements)} products using {tag}.{class_name}")
                return tag_elements
        
        # Strategy 3: Fallback - look for links with product patterns
        all_links = soup.find_all('a', href=True)
        product_links = []
        
        for link in all_links:
            if isinstance(link, Tag):
                href_attr = link.get('href')
                text = link.get_text(strip=True)
                
                if href_attr and len(text) > 10:
                    href_str = str(href_attr) if not isinstance(href_attr, list) else str(href_attr[0])
                    if any(pattern in href_str.lower() for pattern in ['gdsale', 'product', 'item']):
                        product_links.append(link)
        
        if product_links:
            print(f"✅ Found {len(product_links)} products using link fallback")
            return product_links[:20]  # Limit fallback results
        
        return []
    
    # Replace the _parse_yahoo_product method with this fixed version:

    def _parse_yahoo_product(self, item: Tag) -> Optional[Dict]:
        """Parse individual Yahoo product - Fixed version"""
        try:
            if not isinstance(item, Tag):
                return None

            # Get all text content first
            full_text = item.get_text(strip=True)

            # Extract name - NEW STRATEGY: Parse from the text content
            name = ""

            # The debug shows product names are in format: "比較找相似[PRODUCT NAME]$[PRICE]"
            # Let's extract the product name from this pattern

            # Strategy 1: Remove "比較找相似" prefix and extract until price
            if "比較找相似" in full_text:
                text_after_prefix = full_text.replace("比較找相似", "").strip()

                # Extract everything before the price (indicated by $ or numbers)
                # Look for pattern before price indicators
                name_match = re.search(r'^([^$]+?)(?:\$|\d+,\d+)', text_after_prefix)
                if name_match:
                    name = name_match.group(1).strip()

            # Strategy 2: If no "比較找相似", try to extract iPhone product name directly
            if not name and "iPhone" in full_text:
                # Extract iPhone product description
                iphone_match = re.search(r'(iPhone[^$]*?)(?:\$|\d+,\d+)', full_text)
                if iphone_match:
                    name = iphone_match.group(1).strip()

            # Strategy 3: Fallback - use first meaningful chunk of text
            if not name:
                # Split by common separators and take first meaningful part
                parts = re.split(r'[\$]|\d+,\d+', full_text)
                if parts and len(parts[0].strip()) > 10:
                    name = parts[0].strip()[:100]

            # Clean the name
            if name:
                # Remove common prefixes and suffixes
                name = re.sub(r'^(比較找相似|馬上比買|全新品未拆封|品況優)', '', name)
                name = re.sub(r'(贈品\d+.*|限時下殺.*|商店.*)$', '', name)
                name = name.strip()

            # Quality check
            if not name or len(name.strip()) < 5:
                return None

            # Extract price from text
            price = 0.0
            # Look for price patterns in the full text
            price_patterns = [
                r'\$(\d{1,3}(?:,\d{3})*)',  # $25,990
                r'(\d{1,3}(?:,\d{3})*)\$',  # 25,990$
                r'(\d{1,3}(?:,\d{3})*)元',  # 25990元
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, full_text)
                for match in matches:
                    try:
                        potential_price = float(match.replace(',', ''))
                        if 100 <= potential_price <= 100000:  # Reasonable iPhone price range
                            price = potential_price
                            break
                    except:
                        continue
                if price > 0:
                    break
                
            # Extract URL
            url = ""
            if item.name == 'a' and item.get('href'):
                href_attr = item.get('href')
                if href_attr:
                    href_str = str(href_attr) if not isinstance(href_attr, list) else str(href_attr[0])

                    if href_str.startswith('http'):
                        url = href_str
                    elif href_str.startswith('/'):
                        url = self.base_url + href_str

            # Clean name one more time
            name = name[:200]

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

        except Exception as e:
            print(f"❌ Error parsing Yahoo product: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        try:
            # Remove all non-digit characters except decimal point
            price_str = re.sub(r'[^\d.]', '', str(price_text))
            return float(price_str) if price_str else 0.0
        except:
            return 0.0
    
    def _extract_image_url(self, item: Tag) -> str:
        """Extract product image URL"""
        try:
            img_elem = item.find('img')
            if isinstance(img_elem, Tag):
                src_attrs = ['src', 'data-src', 'data-original', 'data-lazy']
                for attr in src_attrs:
                    src_attr = img_elem.get(attr)
                    if src_attr:
                        src = str(src_attr) if not isinstance(src_attr, list) else str(src_attr[0])
                        if src and src.startswith('http'):
                            return src
        except:
            pass
        return ""
    
    def _extract_brand(self, name: str) -> str:
        """Extract brand from product name"""
        brands = ['Apple', 'Samsung', 'ASUS', 'Acer', 'MSI', 'Lenovo', 'HP', 'Dell', 'Nike', 'Adidas', 'Sony', 'LG']
        name_upper = str(name).upper()
        
        for brand in brands:
            if brand.upper() in name_upper:
                return brand
        return ""
    
    def _generate_product_id(self, name: str, url: str) -> str:
        """Generate unique product ID"""
        import hashlib
        source = str(url) if url else str(name)
        return hashlib.md5(source.encode()).hexdigest()[:12]
    
    def _create_empty_product(self, url: str) -> Dict:
        """Create empty product structure"""
        return {
            'platform': self.platform,
            'product_id': 'unknown',
            'name': 'Unknown Yahoo Product',
            'price': 0.0,
            'original_price': 0.0,
            'url': url,
            'image_url': '',
            'brand': '',
            'description': '',
            'availability': False,
            'category': None
        }