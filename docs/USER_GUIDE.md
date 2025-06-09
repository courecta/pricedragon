# PriceDragon System Documentation

## Overview

PriceDragon is a comprehensive price comparison system for Taiwan e-commerce platforms. It provides real-time price tracking, product comparison, and analytics through both API and web interfaces.

## System Architecture

### Components
- **API Server**: RESTful API built with FastAPI
- **Web Dashboard**: Interactive Streamlit interface
- **Database**: SQLite with performance optimizations
- **ETL Pipeline**: Automated data collection and processing
- **Monitoring System**: Health checks and performance tracking

### Current Status
- **API Server**: Running on http://localhost:8000
- **Web Dashboard**: Running on http://localhost:8501
- **Database**: 55 products across 3 platforms (PChome, Momo, Yahoo)
- **Performance**: Optimized with indexes and caching

## API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
Currently no authentication required (development mode)

### Endpoints

#### Health Check
```http
GET /health
```
Returns system health status.

#### Products

##### Get All Products
```http
GET /products/
```
Query Parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100)
- `platform`: Filter by platform name
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `available_only`: Show only available products (default: true)

##### Get Product by ID
```http
GET /products/{product_id}
```

##### Search Products
```http
GET /products/search
```
Query Parameters:
- `q`: Search query
- `platform`: Platform filter
- `min_price`: Minimum price
- `max_price`: Maximum price
- `limit`: Maximum results (default: 50)

#### Price History

##### Get Product Price History
```http
GET /history/{product_id}
```
Query Parameters:
- `days`: Number of days to look back (default: 30)

##### Get Platform Price Trends
```http
GET /history/platform/{platform_name}
```
Query Parameters:
- `days`: Number of days (default: 7)

#### Product Comparison

##### Find Similar Products
```http
GET /comparison/similar/{product_id}
```
Query Parameters:
- `threshold`: Similarity threshold 0-1 (default: 0.6)
- `limit`: Maximum results (default: 10)

##### Find Best Price
```http
GET /comparison/best-price/{product_name}
```
Returns best prices across all platforms for a product.

##### Price Drop Alerts
```http
GET /comparison/price-alerts
```
Query Parameters:
- `days`: Days to check (default: 7)
- `threshold_percent`: Price drop threshold (default: 10.0)

## Web Dashboard Usage

### Access
Navigate to http://localhost:8501 in your web browser.

### Features

#### 1. Home/Search Page
- **Product Search**: Search across all platforms
- **Advanced Filters**: Price range, platform, availability
- **Sorting Options**: Price, name, popularity
- **Product Cards**: Visual product display with prices and links

#### 2. Smart Compare Page
- **Similar Products**: Find products across platforms
- **Price Comparison**: Side-by-side price analysis
- **Feature Comparison**: Compare product specifications
- **Best Deals**: Highlight lowest prices

#### 3. Price Alerts Page
- **Price Drop Detection**: Find recent price reductions
- **Savings Calculator**: Calculate potential savings
- **Alert Configuration**: Set custom thresholds
- **Historical Trends**: Price movement over time

#### 4. Market Analytics Page
- **Platform Statistics**: Performance metrics by platform
- **Price Trends**: Market trend analysis
- **Category Analysis**: Product distribution
- **Performance Metrics**: System health indicators

### Navigation
Use the sidebar menu to switch between different pages and features.

## Database Schema

### Core Tables

#### Products
- `id`: Primary key
- `name`: Product name
- `normalized_name`: Cleaned name for matching
- `platform_id`: Foreign key to platforms
- `platform_product_id`: Platform-specific ID
- `current_price`: Current price
- `original_price`: Original/list price
- `brand`: Product brand
- `url`: Product URL
- `image_url`: Product image
- `is_available`: Availability status

#### Platforms
- `id`: Primary key
- `name`: Platform identifier (pchome, momo, yahoo)
- `display_name`: User-friendly name
- `base_url`: Platform base URL
- `is_active`: Active status

#### Price History
- `id`: Primary key
- `product_id`: Foreign key to products
- `platform_id`: Foreign key to platforms
- `price`: Historical price
- `scraped_at`: Timestamp

#### Product Matches
- `id`: Primary key
- `product_a_id`: First product
- `product_b_id`: Second product
- `similarity_score`: Matching confidence (0-1)
- `match_type`: Type of match (exact, similar, variant)

## Performance Optimizations

### Database Indexes
- Product search indexes (name, brand, platform)
- Price range indexes for filtering
- Historical data indexes for time-series queries
- Similarity matching indexes

### Caching
- Streamlit component caching
- API response caching
- Database query optimization

### SQLite Settings
- WAL journal mode for better concurrency
- Increased cache size (10,000 pages)
- Memory-mapped I/O enabled
- Optimized synchronization settings

## System Monitoring

### Health Endpoints
- `/health`: Basic health check
- API response time monitoring
- Database connection health

### Performance Metrics
- Total products: 55
- Available products: 35
- Active platforms: 3
- Price history records: 55
- Product matches: 341
- Average price: NT$26,888

### Automated Monitoring
The system includes automated health checks and performance monitoring. Check the logs directory for detailed system metrics.

## Deployment

### Development Setup
1. **Start API Server**:
   ```bash
   cd /home/courecta/pricedragon
   python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Dashboard**:
   ```bash
   cd /home/courecta/pricedragon
   streamlit run dashboard/enhanced_main.py --server.port 8501 --server.address 0.0.0.0
   ```

### Production Considerations
- Configure proper authentication
- Set up HTTPS/SSL certificates
- Use production database (PostgreSQL)
- Implement rate limiting
- Set up log rotation
- Configure monitoring alerts

## Troubleshooting

### Common Issues

#### API Not Responding
- Check if uvicorn process is running
- Verify port 8000 is not in use
- Check database connection

#### Dashboard Loading Issues
- Ensure Streamlit is installed
- Check port 8501 availability
- Verify API endpoint connectivity

#### Database Errors
- Check database file permissions
- Verify SQLite installation
- Run database optimization script

#### Performance Issues
- Run performance optimization script
- Check system resources
- Review query performance logs

### Error Logs
Check the `logs/` directory for detailed error information and system diagnostics.

## API Examples

### Python Client Example
```python
import requests

# Get all products
response = requests.get('http://localhost:8000/products/')
products = response.json()

# Search for iPhone products
response = requests.get('http://localhost:8000/products/search', 
                       params={'q': 'iPhone', 'limit': 10})
search_results = response.json()

# Get price history
response = requests.get('http://localhost:8000/history/1', 
                       params={'days': 30})
price_history = response.json()
```

### JavaScript/Node.js Example
```javascript
const axios = require('axios');

// Get products
async function getProducts() {
    try {
        const response = await axios.get('http://localhost:8000/products/');
        return response.data;
    } catch (error) {
        console.error('Error:', error);
    }
}

// Search products
async function searchProducts(query) {
    try {
        const response = await axios.get('http://localhost:8000/products/search', {
            params: { q: query, limit: 20 }
        });
        return response.data;
    } catch (error) {
        console.error('Error:', error);
    }
}
```

## Support

For technical support or feature requests, please check the system logs and monitoring dashboard for diagnostic information.

---

*Generated on: June 8, 2025*
*System Version: 0.1.0*
