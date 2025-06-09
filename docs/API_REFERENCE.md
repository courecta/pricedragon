# PriceDragon API Reference

## Authentication
Currently in development mode - no authentication required.

## Base URL
```
http://localhost:8000
```

## Response Format
All API responses follow this format:
```json
{
  "data": [...],
  "message": "Success",
  "status": 200
}
```

Error responses:
```json
{
  "detail": "Error message",
  "status": 400/404/500
}
```

## Endpoints

### System Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

#### API Information
```http
GET /
```

**Response:**
```json
{
  "message": "PriceDragon API is running!",
  "version": "0.1.0",
  "docs": "/docs"
}
```

### Product Endpoints

#### Get All Products
```http
GET /products/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Number of records to skip |
| limit | integer | 100 | Maximum records to return |
| platform | string | null | Filter by platform name |
| min_price | float | null | Minimum price filter |
| max_price | float | null | Maximum price filter |
| available_only | boolean | true | Show only available products |

**Example Request:**
```bash
curl "http://localhost:8000/products/?platform=pchome&min_price=1000&max_price=50000&limit=10"
```

**Response:**
```json
[
  {
    "id": 1,
    "platform": "pchome",
    "product_id": "DGAY4F-A900HXWL4",
    "name": "Apple iPhone 15 Pro 128GB",
    "price": 35900.0,
    "original_price": 39900.0,
    "url": "https://24h.pchome.com.tw/prod/DGAY4F-A900HXWL4",
    "image_url": "https://...",
    "brand": "Apple",
    "description": "Latest iPhone with titanium design",
    "availability": true,
    "created_at": "2025-06-08T10:30:00",
    "updated_at": "2025-06-08T18:15:00"
  }
]
```

#### Get Product by ID
```http
GET /products/{product_id}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| product_id | integer | Product ID |

**Example Request:**
```bash
curl "http://localhost:8000/products/1"
```

**Response:**
```json
{
  "id": 1,
  "platform": "pchome",
  "product_id": "DGAY4F-A900HXWL4",
  "name": "Apple iPhone 15 Pro 128GB",
  "price": 35900.0,
  "original_price": 39900.0,
  "url": "https://24h.pchome.com.tw/prod/DGAY4F-A900HXWL4",
  "image_url": "https://...",
  "brand": "Apple",
  "description": "Latest iPhone with titanium design",
  "availability": true,
  "created_at": "2025-06-08T10:30:00",
  "updated_at": "2025-06-08T18:15:00"
}
```

#### Search Products
```http
GET /products/search
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| q | string | required | Search query |
| platform | string | null | Platform filter |
| min_price | float | null | Minimum price |
| max_price | float | null | Maximum price |
| limit | integer | 50 | Maximum results |

**Example Request:**
```bash
curl "http://localhost:8000/products/search?q=iPhone&platform=pchome&limit=5"
```

**Response:**
```json
{
  "query": "iPhone",
  "total_found": 15,
  "results": [
    {
      "id": 1,
      "platform": "pchome",
      "name": "Apple iPhone 15 Pro 128GB",
      "price": 35900.0,
      "relevance_score": 0.95
    }
  ]
}
```

### Price History Endpoints

#### Get Product Price History
```http
GET /history/{product_id}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| product_id | integer | Product ID |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | integer | 30 | Number of days to look back |

**Example Request:**
```bash
curl "http://localhost:8000/history/1?days=7"
```

**Response:**
```json
{
  "product_id": 1,
  "product_name": "Apple iPhone 15 Pro 128GB",
  "platform": "pchome",
  "days_requested": 7,
  "price_points": [
    {
      "price": 35900.0,
      "scraped_at": "2025-06-08T18:15:00",
      "change_from_previous": -500.0,
      "change_percentage": -1.37
    },
    {
      "price": 36400.0,
      "scraped_at": "2025-06-07T18:15:00",
      "change_from_previous": 0.0,
      "change_percentage": 0.0
    }
  ],
  "statistics": {
    "current_price": 35900.0,
    "lowest_price": 35900.0,
    "highest_price": 36400.0,
    "average_price": 36150.0,
    "total_change": -500.0,
    "total_change_percentage": -1.37
  }
}
```

#### Get Platform Price Trends
```http
GET /history/platform/{platform_name}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| platform_name | string | Platform name (pchome, momo, yahoo) |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | integer | 7 | Number of days |

**Example Request:**
```bash
curl "http://localhost:8000/history/platform/pchome?days=7"
```

**Response:**
```json
{
  "platform": "pchome",
  "days_analyzed": 7,
  "total_products": 25,
  "price_changes": [
    {
      "date": "2025-06-08",
      "average_price": 28500.50,
      "products_updated": 12,
      "price_drops": 3,
      "price_increases": 2
    }
  ],
  "summary": {
    "average_price_change": -2.5,
    "products_with_drops": 8,
    "products_with_increases": 5,
    "stable_products": 12
  }
}
```

### Comparison Endpoints

#### Find Similar Products
```http
GET /comparison/similar/{product_id}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| product_id | integer | Source product ID |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| threshold | float | 0.6 | Similarity threshold (0.0-1.0) |
| limit | integer | 10 | Maximum results |

**Example Request:**
```bash
curl "http://localhost:8000/comparison/similar/1?threshold=0.7&limit=5"
```

**Response:**
```json
[
  {
    "id": 15,
    "platform": "momo",
    "product_id": "12345678",
    "name": "Apple iPhone 15 Pro 128GB 紫",
    "price": 35500.0,
    "original_price": 39900.0,
    "url": "https://momo.com/...",
    "brand": "Apple",
    "availability": true,
    "similarity_score": 0.85,
    "price_difference": -400.0,
    "savings": 400.0
  }
]
```

#### Find Best Price
```http
GET /comparison/best-price/{product_name}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| product_name | string | Product name to search |

**Example Request:**
```bash
curl "http://localhost:8000/comparison/best-price/iPhone%2015%20Pro"
```

**Response:**
```json
{
  "query": "iPhone 15 Pro",
  "best_price": 35500.0,
  "total_found": 8,
  "products": [
    {
      "id": 15,
      "platform": "momo",
      "name": "Apple iPhone 15 Pro 128GB",
      "price": 35500.0,
      "original_price": 39900.0,
      "url": "https://momo.com/...",
      "similarity_score": 0.92,
      "brand": "Apple",
      "savings": 4400.0,
      "rank": 1
    },
    {
      "id": 1,
      "platform": "pchome",
      "name": "Apple iPhone 15 Pro 128GB",
      "price": 35900.0,
      "original_price": 39900.0,
      "url": "https://24h.pchome.com.tw/...",
      "similarity_score": 0.95,
      "brand": "Apple",
      "savings": 4000.0,
      "rank": 2
    }
  ]
}
```

#### Get Price Drop Alerts
```http
GET /comparison/price-alerts
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | integer | 7 | Number of days to check |
| threshold_percent | float | 10.0 | Price drop threshold percentage |

**Example Request:**
```bash
curl "http://localhost:8000/comparison/price-alerts?days=3&threshold_percent=15"
```

**Response:**
```json
{
  "alerts_found": 5,
  "threshold_percent": 15.0,
  "days_checked": 3,
  "price_drops": [
    {
      "id": 23,
      "platform": "yahoo",
      "name": "Sony WH-1000XM5 耳機",
      "current_price": 8990.0,
      "original_price": 10990.0,
      "price_drop_percent": 18.2,
      "savings": 2000.0,
      "url": "https://tw.buy.yahoo.com/...",
      "updated_at": "2025-06-08T15:30:00"
    }
  ]
}
```

## Error Handling

### Error Codes
- `400`: Bad Request - Invalid parameters
- `404`: Not Found - Resource doesn't exist
- `422`: Validation Error - Invalid data format
- `500`: Internal Server Error - Server-side error

### Error Response Format
```json
{
  "detail": "Product not found",
  "status": 404,
  "timestamp": "2025-06-08T18:30:00Z"
}
```

### Common Error Messages
- `"Product not found"`: Product ID doesn't exist
- `"Platform not supported"`: Invalid platform name
- `"Invalid price range"`: min_price > max_price
- `"Search query too short"`: Query less than 2 characters
- `"Limit exceeds maximum"`: Limit > 100

## Rate Limiting
Currently no rate limiting in development mode. Production deployment will include:
- 100 requests per minute per IP
- 1000 requests per hour per API key

## SDK Examples

### Python
```python
import requests
from typing import Optional, List, Dict

class PriceDragonAPI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def get_products(self, skip: int = 0, limit: int = 100, 
                    platform: Optional[str] = None) -> List[Dict]:
        params = {"skip": skip, "limit": limit}
        if platform:
            params["platform"] = platform
        
        response = requests.get(f"{self.base_url}/products/", params=params)
        response.raise_for_status()
        return response.json()
    
    def search_products(self, query: str, limit: int = 50) -> Dict:
        params = {"q": query, "limit": limit}
        response = requests.get(f"{self.base_url}/products/search", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_price_history(self, product_id: int, days: int = 30) -> Dict:
        params = {"days": days}
        response = requests.get(f"{self.base_url}/history/{product_id}", params=params)
        response.raise_for_status()
        return response.json()

# Usage
api = PriceDragonAPI()
products = api.get_products(platform="pchome", limit=10)
search_results = api.search_products("iPhone")
price_history = api.get_price_history(1, days=7)
```

### JavaScript/Node.js
```javascript
class PriceDragonAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async getProducts(options = {}) {
        const params = new URLSearchParams(options);
        const response = await fetch(`${this.baseUrl}/products/?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async searchProducts(query, limit = 50) {
        const params = new URLSearchParams({ q: query, limit });
        const response = await fetch(`${this.baseUrl}/products/search?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async getPriceHistory(productId, days = 30) {
        const params = new URLSearchParams({ days });
        const response = await fetch(`${this.baseUrl}/history/${productId}?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
}

// Usage
const api = new PriceDragonAPI();

// Get products
const products = await api.getProducts({ platform: 'pchome', limit: 10 });

// Search
const searchResults = await api.searchProducts('iPhone');

// Price history
const priceHistory = await api.getPriceHistory(1, 7);
```

### cURL Examples

#### Basic Product Search
```bash
# Search for laptops under NT$30,000
curl -X GET "http://localhost:8000/products/search?q=laptop&max_price=30000&limit=10" \
     -H "Accept: application/json"
```

#### Get Price History with Formatting
```bash
# Get 30-day price history
curl -X GET "http://localhost:8000/history/1?days=30" \
     -H "Accept: application/json" | jq .
```

#### Find Similar Products
```bash
# Find similar products with high confidence
curl -X GET "http://localhost:8000/comparison/similar/1?threshold=0.8&limit=5" \
     -H "Accept: application/json"
```

## Testing

### API Testing
Use the interactive API documentation at http://localhost:8000/docs to test endpoints.

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

---

*Last Updated: June 8, 2025*
*API Version: 0.1.0*
