"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import products, history, comparison

app = FastAPI(
    title="PriceDragon API",
    description="REST API for Taiwan E-Commerce Price Comparison",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(history.router, prefix="/history", tags=["Price History"])
app.include_router(comparison.router, prefix="/comparison", tags=["Product Comparison"])

@app.get("/")
def read_root():
    """API health check"""
    return {
        "message": "PriceDragon API is running!",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}