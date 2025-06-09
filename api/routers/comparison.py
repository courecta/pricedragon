"""Product comparison API endpoints"""
from fastapi import APIRouter, HTTPException, Depends, Query
from database.db_utils import DatabaseManager
from database.models import Product, ProductMatch
from api.schemas import ProductResponse
from typing import List, Optional
import difflib

router = APIRouter()

def get_db():
    """Dependency to get database manager"""
    return DatabaseManager()

@router.get("/similar/{product_id}", response_model=List[ProductResponse])
def get_similar_products(
    product_id: int,
    threshold: float = Query(0.6, ge=0.0, le=1.0, description="Similarity threshold"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: DatabaseManager = Depends(get_db)
):
    """Find similar products across platforms"""
    try:
        session = db.get_session()
        
        try:
            # Get the source product
            source_product = session.query(Product).filter_by(id=product_id).first()
            if not source_product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Find existing matches
            matches = session.query(ProductMatch).filter(
                (ProductMatch.product_a_id == product_id) | 
                (ProductMatch.product_b_id == product_id)
            ).filter(ProductMatch.similarity_score >= threshold).all()
            
            similar_products = []
            
            for match in matches:
                # Get the other product in the match
                other_product_id = match.product_b_id if match.product_a_id == product_id else match.product_a_id
                other_product = session.query(Product).filter_by(id=other_product_id).first()
                
                if other_product and other_product.platform:
                    product_dict = {
                        'id': other_product.id,
                        'platform': other_product.platform.name,
                        'product_id': other_product.platform_product_id,
                        'name': other_product.name,
                        'price': other_product.current_price,
                        'original_price': other_product.original_price,
                        'url': other_product.url,
                        'image_url': other_product.image_url,
                        'brand': other_product.brand,
                        'description': other_product.description,
                        'availability': other_product.is_available,
                        'created_at': other_product.created_at,
                        'updated_at': other_product.updated_at
                    }
                    similar_products.append(ProductResponse(**product_dict))
            
            return similar_products[:limit]
            
        finally:
            session.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar products: {str(e)}")

@router.get("/best-price/{product_name}")
def find_best_price(
    product_name: str,
    db: DatabaseManager = Depends(get_db)
):
    """Find the best price for a product across all platforms"""
    try:
        session = db.get_session()
        
        try:
            # Search for products with similar names
            products = session.query(Product).filter(
                Product.name.contains(product_name)
            ).filter(Product.is_available == True).all()
            
            if not products:
                raise HTTPException(status_code=404, detail=f"No products found matching '{product_name}'")
            
            # Use difflib to find the most similar products
            similar_products = []
            for product in products:
                similarity = difflib.SequenceMatcher(None, product_name.lower(), product.name.lower()).ratio()
                if similarity > 0.5:  # At least 50% similar
                    similar_products.append((product, similarity))
            
            # Sort by similarity and price
            similar_products.sort(key=lambda x: (-x[1], x[0].current_price or float('inf')))
            
            # Format response
            result = []
            for product, similarity in similar_products[:10]:
                if product.platform:
                    result.append({
                        'id': product.id,
                        'platform': product.platform.name,
                        'product_id': product.platform_product_id,
                        'name': product.name,
                        'price': product.current_price,
                        'original_price': product.original_price,
                        'url': product.url,
                        'similarity_score': round(similarity, 3),
                        'brand': product.brand,
                        'availability': product.is_available
                    })
            
            if result:
                return {
                    'query': product_name,
                    'best_price': min(p['price'] for p in result if p['price']),
                    'total_found': len(result),
                    'products': result
                }
            else:
                raise HTTPException(status_code=404, detail="No similar products found")
            
        finally:
            session.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find best price: {str(e)}")

@router.get("/price-alerts")
def get_price_drop_alerts(
    days: int = Query(7, ge=1, le=30, description="Number of days to check"),
    threshold_percent: float = Query(10.0, ge=1.0, le=50.0, description="Price drop threshold percentage"),
    db: DatabaseManager = Depends(get_db)
):
    """Get products with significant price drops"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import and_, func
        
        session = db.get_session()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # This is a simplified version - in production you'd want more sophisticated price tracking
            recent_products = session.query(Product).filter(
                and_(
                    Product.original_price.isnot(None),
                    Product.current_price.isnot(None),
                    Product.current_price < Product.original_price,
                    Product.updated_at >= cutoff_date
                )
            ).all()
            
            price_drops = []
            for product in recent_products:
                if product.current_price and product.original_price:
                    drop_percent = ((product.original_price - product.current_price) / product.original_price) * 100
                    
                    if drop_percent >= threshold_percent and product.platform:
                        price_drops.append({
                            'id': product.id,
                            'platform': product.platform.name,
                            'name': product.name,
                            'current_price': product.current_price,
                            'original_price': product.original_price,
                            'price_drop_percent': round(drop_percent, 1),
                            'savings': product.original_price - product.current_price,
                            'url': product.url,
                            'updated_at': product.updated_at
                        })
            
            # Sort by price drop percentage
            price_drops.sort(key=lambda x: x['price_drop_percent'], reverse=True)
            
            return {
                'alerts_found': len(price_drops),
                'threshold_percent': threshold_percent,
                'days_checked': days,
                'price_drops': price_drops[:20]  # Limit to top 20
            }
            
        finally:
            session.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get price alerts: {str(e)}")
