"""Product API endpoints"""
from fastapi import APIRouter, Query, HTTPException, Depends
from database.db_utils import DatabaseManager
from database.models import Product, Platform
from api.schemas import ProductResponse, SearchResponse
from typing import List, Optional

router = APIRouter()

def get_db():
    """Dependency to get database manager"""
    return DatabaseManager()

def convert_product_to_dict(product):
    """Convert SQLAlchemy Product to dictionary while session is active"""
    return {
        'id': product.id,
        'platform': product.platform.name if product.platform else 'unknown',
        'product_id': product.platform_product_id,
        'name': product.name,
        'price': product.current_price,
        'original_price': product.original_price,
        'url': product.url,
        'image_url': product.image_url,
        'brand': product.brand,
        'description': product.description,
        'availability': product.is_available,
        'created_at': product.created_at,
        'updated_at': product.updated_at
    }

@router.get("/search", response_model=SearchResponse)
def search_products(
    q: str = Query(..., description="Search query", min_length=1),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    db: DatabaseManager = Depends(get_db)
):
    """Search products with filters and pagination"""
    try:
        # Fix: Manage session ourselves to avoid early closure
        session = db.get_session()
        
        try:
            # Query products directly with session
            query = session.query(Product).filter(Product.name.contains(q))
            
            # Apply filters if provided
            if platform:
                query = query.join(Product.platform).filter(Platform.name == platform)
            if min_price is not None:
                query = query.filter(Product.current_price >= min_price)
            if max_price is not None:
                query = query.filter(Product.current_price <= max_price)
            
            # Apply pagination
            offset = (page - 1) * per_page
            products = query.order_by(Product.current_price.asc()).offset(offset).limit(per_page).all()
            
            # Convert to dictionaries while session is still open
            product_responses = []
            for product in products:
                product_dict = convert_product_to_dict(product)
                product_responses.append(ProductResponse(**product_dict))
            
            # Get total count for pagination
            total = query.count()
            has_next = (offset + per_page) < total
            has_prev = page > 1
            
            return SearchResponse(
                products=product_responses,
                total=total,
                page=page,
                per_page=per_page,
                has_next=has_next,
                has_prev=has_prev
            )
            
        finally:
            # Always close session
            session.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/{platform}/{product_id}", response_model=ProductResponse)
def get_product(
    platform: str,
    product_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """Get specific product details"""
    try:
        session = db.get_session()
        
        try:
            product = session.query(Product).join(Product.platform).filter(
                Platform.name == platform,
                Product.platform_product_id == product_id
            ).first()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Convert to dict while session is open
            product_dict = convert_product_to_dict(product)
            return ProductResponse(**product_dict)
            
        finally:
            session.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")

@router.get("/", response_model=List[ProductResponse])
def list_products(
    limit: int = Query(50, ge=1, le=100, description="Number of products to return"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    db: DatabaseManager = Depends(get_db)
):
    """List recent products"""
    try:
        session = db.get_session()
        
        try:
            query = session.query(Product)
            
            if platform:
                query = query.join(Product.platform).filter(Platform.name == platform)
            
            products = query.order_by(Product.created_at.desc()).limit(limit).all()
            
            # Convert to dicts while session is open
            product_responses = []
            for product in products:
                product_dict = convert_product_to_dict(product)
                product_responses.append(ProductResponse(**product_dict))
            
            return product_responses
            
        finally:
            session.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list products: {str(e)}")