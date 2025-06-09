"""Data transformation utilities"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import re
import logging
from .schemas import ProductSchema

class DataTransformer:
    """Handles data cleaning and transformation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common brand mappings for normalization
        self.brand_mappings = {
            'apple': 'Apple',
            'samsung': 'Samsung',
            'sony': 'Sony',
            'lg': 'LG',
            'htc': 'HTC',
            'asus': 'ASUS',
            'acer': 'Acer',
            'msi': 'MSI',
            'gigabyte': 'Gigabyte',
            'xiaomi': 'Xiaomi',
            'oppo': 'OPPO',
            'vivo': 'Vivo'
        }
        
        # Price anomaly detection thresholds
        self.price_thresholds = {
            'min_price': 1.0,           # Minimum reasonable price
            'max_price': 5_000_000.0,   # Maximum reasonable price
            'discount_threshold': 0.9    # Max 90% discount seems reasonable
        }
    
    def transform_product_batch(self, raw_products: List[Dict[str, Any]], source: str) -> Tuple[List[Dict], List[str]]:
        """Transform a batch of raw product data"""
        transformed_products = []
        errors = []
        
        for i, raw_product in enumerate(raw_products):
            try:
                transformed = self._transform_single_product(raw_product, source)
                if transformed:
                    transformed_products.append(transformed)
            except Exception as e:
                error_msg = f"Failed to transform product {i+1}: {str(e)}"
                errors.append(error_msg)
                self.logger.warning(error_msg)
        
        return transformed_products, errors
    
    def _transform_single_product(self, raw_product: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Transform a single product with data cleaning"""
        
        # 1. Add metadata
        raw_product['scraped_at'] = datetime.now(timezone.utc)
        
        # 2. Normalize brand names
        if 'brand' in raw_product and raw_product['brand']:
            raw_product['brand'] = self._normalize_brand(raw_product['brand'])
        
        # 3. Clean and enhance product name
        if 'name' in raw_product:
            raw_product['name'] = self._enhance_product_name(raw_product['name'])
        
        # 4. Validate and adjust prices
        raw_product = self._validate_prices(raw_product)
        
        # 5. Generate additional fields
        raw_product = self._add_derived_fields(raw_product)
        
        return raw_product
    
    def _normalize_brand(self, brand: str) -> str:
        """Normalize brand names to consistent format"""
        brand_lower = brand.lower().strip()
        
        # Check direct mappings
        if brand_lower in self.brand_mappings:
            return self.brand_mappings[brand_lower]
        
        # Check if brand contains a known brand
        for key, value in self.brand_mappings.items():
            if key in brand_lower:
                return value
        
        # Return title case if no mapping found
        return brand.title().strip()
    
    def _enhance_product_name(self, name: str) -> str:
        """Enhanced product name cleaning"""
        # Remove excessive punctuation
        name = re.sub(r'[!]{2,}', '!', name)
        name = re.sub(r'[?]{2,}', '?', name)
        
        # Normalize model numbers (iPhone15 -> iPhone 15)
        name = re.sub(r'(iPhone)(\d+)', r'\1 \2', name)
        name = re.sub(r'(Galaxy)([A-Z]\d+)', r'\1 \2', name)
        name = re.sub(r'(Pixel)(\d+)', r'\1 \2', name)
        
        # Normalize storage sizes
        name = re.sub(r'(\d+)(GB|TB)', r'\1 \2', name)
        name = re.sub(r'(\d+)(g|t)(?=\s|$)', r'\1\2B', name, flags=re.IGNORECASE)
        
        # Clean up spacing
        name = ' '.join(name.split())
        
        return name
    
    def _validate_prices(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and potentially adjust price data"""
        price = product.get('price', 0)
        original_price = product.get('original_price')
        
        # Flag potential price anomalies
        if price < self.price_thresholds['min_price']:
            self.logger.warning(f"Suspiciously low price: {price} for {product.get('name')}")
        
        if price > self.price_thresholds['max_price']:
            self.logger.warning(f"Suspiciously high price: {price} for {product.get('name')}")
        
        # Check discount reasonableness
        if original_price and original_price > 0 and price > 0:
            discount_ratio = price / original_price
            if discount_ratio < (1 - self.price_thresholds['discount_threshold']):
                self.logger.warning(f"Large discount detected: {discount_ratio:.1%} for {product.get('name')}")
        
        return product
    
    def _add_derived_fields(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Add derived fields for analytics"""
        
        # Add price category
        price = product.get('price', 0)
        if price < 1000:
            product['price_category'] = 'budget'
        elif price < 10000:
            product['price_category'] = 'mid-range'
        elif price < 50000:
            product['price_category'] = 'premium'
        else:
            product['price_category'] = 'luxury'
        
        # Extract potential model information from name
        name = product.get('name', '')
        
        # iPhone model detection
        iphone_match = re.search(r'iPhone\s*(\d+(?:\s*Pro)?(?:\s*Max)?)', name, re.IGNORECASE)
        if iphone_match:
            product['model'] = f"iPhone {iphone_match.group(1)}"
        
        # Storage size detection
        storage_match = re.search(r'(\d+)\s*(GB|TB)', name, re.IGNORECASE)
        if storage_match:
            size = int(storage_match.group(1))
            unit = storage_match.group(2).upper()
            if unit == 'TB':
                size *= 1024  # Convert to GB
            product['storage_gb'] = size
        
        return product