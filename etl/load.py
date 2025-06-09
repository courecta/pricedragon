"""ETL Load pipeline with enhanced error handling and metrics"""
from database.db_utils import DatabaseManager
from .schemas import ProductSchema, BulkProductSchema
from .transform import DataTransformer
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
from dataclasses import dataclass, field

@dataclass
class LoadResult:
    """Result object for load operations"""
    success_count: int = 0
    failed_count: int = 0
    duplicate_count: int = 0
    validation_errors: List[str] = field(default_factory=list)
    transformation_errors: List[str] = field(default_factory=list)
    database_errors: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    
    @property
    def total_processed(self) -> int:
        return self.success_count + self.failed_count
    
    @property
    def success_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return self.success_count / self.total_processed

class DataLoader:
    """Enhanced data loader with comprehensive error handling"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.db = DatabaseManager(database_url)
        self.transformer = DataTransformer()
        self.logger = logging.getLogger(__name__)
    
    def load_products(self, raw_products: List[Dict[str, Any]], source: str = "unknown") -> LoadResult:
        """Load products with full ETL pipeline"""
        start_time = datetime.now()
        result = LoadResult()
        
        try:
            # Step 1: Transform raw data
            self.logger.info(f"Starting ETL for {len(raw_products)} products from {source}")
            
            transformed_products, transformation_errors = self.transformer.transform_product_batch(
                raw_products, source
            )
            result.transformation_errors = transformation_errors
            
            if not transformed_products:
                self.logger.warning("No products survived transformation")
                return result
            
            # Step 2: Validate transformed data
            validated_products, validation_errors = self._validate_products(transformed_products)
            result.validation_errors = validation_errors
            
            # Step 3: Load into database
            if validated_products:
                db_result = self._load_to_database(validated_products)
                result.success_count = db_result['success']
                result.failed_count = db_result['failed']
                result.duplicate_count = db_result['duplicates']
                result.database_errors = db_result['errors']
            
            # Calculate metrics
            end_time = datetime.now()
            result.processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Log summary
            self._log_load_summary(result, source)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Critical error in ETL pipeline: {e}")
            result.database_errors.append(f"Pipeline failure: {str(e)}")
            return result
    
    def _validate_products(self, products: List[Dict[str, Any]]) -> tuple[List[Dict], List[str]]:
        """Validate products using Pydantic schemas"""
        validated_products = []
        errors = []
        
        for i, product_data in enumerate(products):
            try:
                # Validate using Pydantic schema
                validated_product = ProductSchema(**product_data)
                validated_products.append(validated_product.dict())
                
            except Exception as e:
                error_msg = f"Validation failed for product {i+1}: {str(e)}"
                errors.append(error_msg)
                self.logger.warning(error_msg)
        
        return validated_products, errors
    
    def _load_to_database(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load validated products to database"""
        try:
            saved_count = self.db.save_products(products)
            
            return {
                'success': saved_count,
                'failed': 0,
                'duplicates': 0,  # DatabaseManager handles upserts
                'errors': []
            }
            
        except Exception as e:
            self.logger.error(f"Database load failed: {e}")
            return {
                'success': 0,
                'failed': len(products),
                'duplicates': 0,
                'errors': [f"Database error: {str(e)}"]
            }
    
    def _log_load_summary(self, result: LoadResult, source: str):
        """Log comprehensive load summary"""
        self.logger.info(f"""
ETL Pipeline Summary for {source}:
  ✅ Success: {result.success_count}
  ❌ Failed: {result.failed_count}
  🔄 Duplicates: {result.duplicate_count}
  📊 Success Rate: {result.success_rate:.1%}
  ⏱️  Processing Time: {result.processing_time_ms}ms
  
Error Breakdown:
  - Transformation: {len(result.transformation_errors)}
  - Validation: {len(result.validation_errors)}
  - Database: {len(result.database_errors)}
        """)