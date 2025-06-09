"""PriceDragon Enhanced Dashboard - Complete E-commerce Price Comparison Platform"""
import streamlit as st
import requests, sys, os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Import our custom components
from dashboard.components.advanced import (
    render_product_comparison_page, 
    render_price_alerts_page, 
    render_analytics_dashboard,
    fetch_similar_products,
    fetch_best_price,
    fetch_price_alerts
)

# Page configuration
st.set_page_config(
    page_title="🐉 PriceDragon - Taiwan Price Comparison",
    page_icon="🐉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    }
    
    .price-highlight {
        font-size: 28px;
        font-weight: bold;
        color: #e74c3c;
        margin: 10px 0;
    }
    
    .platform-badge {
        background: linear-gradient(45deg, #3498db, #2980b9);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    
    .discount-badge {
        background: linear-gradient(45deg, #e74c3c, #c0392b);
        color: white;
        padding: 4px 8px;
        border-radius: 15px;
        font-size: 11px;
        font-weight: bold;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .nav-tab {
        font-size: 16px;
        font-weight: 600;
        padding: 10px 20px;
        margin: 5px;
        border-radius: 25px;
        border: none;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .nav-tab:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Cache functions
@st.cache_data(ttl=300)
def fetch_products(query: str, platform: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, per_page: int = 20) -> Dict:
    """Fetch products from API with caching"""
    try:
        params = {"q": query, "per_page": per_page}
        if platform:
            params["platform"] = platform
        if min_price is not None:
            params["min_price"] = str(min_price)
        if max_price is not None:
            params["max_price"] = str(max_price)
            
        response = requests.get(f"{API_BASE_URL}/products/search", params=params)
        
        if response.status_code == 200:
            return response.json()
        return {"products": [], "total": 0}
    except Exception as e:
        st.error(f"API Error: {e}")
        return {"products": [], "total": 0}

@st.cache_data(ttl=300)
def fetch_recent_products(limit: int = 50) -> List[Dict]:
    """Fetch recent products"""
    try:
        response = requests.get(f"{API_BASE_URL}/products/", params={"limit": limit})
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_price_history(platform: str, product_id: str) -> List[Dict]:
    """Fetch price history for a product"""
    try:
        response = requests.get(f"{API_BASE_URL}/history/{platform}/{product_id}")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

# Utility functions
def format_price(price: float) -> str:
    """Format price with currency"""
    return f"NT${price:,.0f}"

def calculate_savings(original: float, current: float) -> Dict:
    """Calculate savings and discount percentage"""
    if original and current and original > current:
        savings = original - current
        discount_pct = (savings / original) * 100
        return {"savings": savings, "discount_pct": discount_pct}
    return {"savings": 0, "discount_pct": 0}

def create_enhanced_product_card(product: Dict, index: int) -> None:
    """Create an enhanced product display card"""
    with st.container():
        # Create the product card HTML
        card_html = f"""
        <div class="product-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">
                        {product['name'][:80]}{'...' if len(product['name']) > 80 else ''}
                    </h4>
                    <span class="platform-badge">{product['platform'].upper()}</span>
                    {f'<span style="margin-left: 10px; color: #7f8c8d;">Brand: {product["brand"]}</span>' if product.get('brand') else ''}
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Price and action columns
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            current_price = product['price']
            original_price = product.get('original_price')
            
            price_html = f'<div class="price-highlight">{format_price(current_price)}</div>'
            st.markdown(price_html, unsafe_allow_html=True)
            
            if original_price and original_price > current_price:
                savings_data = calculate_savings(original_price, current_price)
                st.markdown(f'<span class="discount-badge">{savings_data["discount_pct"]:.0f}% OFF</span>', 
                           unsafe_allow_html=True)
                st.success(f"Save {format_price(savings_data['savings'])}")
        
        with col2:
            availability = "✅ Available" if product['availability'] else "❌ Out of Stock"
            st.write(availability)
            
            # Quality indicators
            if product.get('image_url'):
                st.write("📷 Image")
            if product.get('description'):
                st.write("📝 Description")
        
        with col3:
            # Action buttons
            if st.button("🔍 Similar", key=f"similar_{index}", help="Find similar products"):
                st.session_state[f"show_similar_{product['id']}"] = True
            
            if st.button("📈 History", key=f"history_{index}", help="View price history"):
                st.session_state[f"show_history_{product['id']}"] = True
        
        with col4:
            if product.get('url'):
                st.markdown(f"[🛒 Buy Now]({product['url']})", help="Go to product page")
            
            # Add to comparison (placeholder for future feature)
            if st.button("➕ Compare", key=f"compare_{index}", help="Add to comparison"):
                if 'comparison_list' not in st.session_state:
                    st.session_state.comparison_list = []
                
                if product not in st.session_state.comparison_list:
                    st.session_state.comparison_list.append(product)
                    st.success("Added to comparison!")
                else:
                    st.info("Already in comparison")
        
        # Show similar products if requested
        if st.session_state.get(f"show_similar_{product['id']}", False):
            with st.expander(f"🔍 Similar Products - {product['name'][:40]}...", expanded=True):
                similar_products = fetch_similar_products(product['id'])
                if similar_products:
                    for sim_product in similar_products[:3]:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"**{sim_product['name'][:60]}...**")
                            st.write(f"Platform: {sim_product['platform']}")
                        with col2:
                            st.write(f"**{format_price(sim_product['price'])}**")
                        with col3:
                            if sim_product.get('url'):
                                st.markdown(f"[🔗 View]({sim_product['url']})")
                else:
                    st.info("No similar products found")
        
        # Show price history if requested
        if st.session_state.get(f"show_history_{product['id']}", False):
            with st.expander(f"📈 Price History - {product['name'][:40]}...", expanded=True):
                history = fetch_price_history(product['platform'], product['product_id'])
                if history:
                    df_history = pd.DataFrame(history)
                    df_history['scraped_at'] = pd.to_datetime(df_history['scraped_at'])
                    
                    fig = px.line(
                        df_history,
                        x='scraped_at',
                        y='price',
                        title=f"Price History",
                        labels={'scraped_at': 'Date', 'price': 'Price (NT$)'}
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No price history available")

def render_main_search_page():
    """Render the main search and comparison page"""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 3rem;">🐉 PriceDragon</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.2rem;">Taiwan's Premier E-commerce Price Comparison Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search interface
    st.markdown("### 🔍 Smart Product Search")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "",
            placeholder="Search for products (e.g., iPhone 15, MacBook Air, Samsung TV...)",
            key="main_search",
            label_visibility="collapsed"
        )
    
    with col2:
        search_clicked = st.button("🔍 Search Products", type="primary", use_container_width=True)
    
    # Advanced filters in expandable section
    with st.expander("🎛️ Advanced Filters"):
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            platforms = ["All", "pchome", "momo", "yahoo", "shopee", "ruten"]
            selected_platform = st.selectbox("Platform", platforms)
            platform_filter = None if selected_platform == "All" else selected_platform
        
        with filter_col2:
            price_range = st.slider(
                "Price Range (NT$)",
                min_value=0,
                max_value=100000,
                value=(0, 50000),
                step=1000
            )
        
        with filter_col3:
            results_per_page = st.selectbox("Results per page", [10, 20, 50], index=1)
    
    # Execute search
    if search_query and (search_clicked or search_query):
        with st.spinner("🐉 Searching across all platforms..."):
            search_results = fetch_products(
                search_query,
                platform_filter,
                float(price_range[0]),
                float(price_range[1]),
                results_per_page
            )
        
        products = search_results.get("products", [])
        total_results = search_results.get("total", 0)
        
        if products:
            # Results summary
            st.markdown("---")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin: 0; color: #3498db;">{total_results}</h3>
                    <p style="margin: 5px 0 0 0;">Products Found</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if products:
                    avg_price = sum(p['price'] for p in products) / len(products)
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="margin: 0; color: #2ecc71;">{format_price(avg_price)}</h3>
                        <p style="margin: 5px 0 0 0;">Average Price</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                if products:
                    min_price = min(p['price'] for p in products)
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="margin: 0; color: #e74c3c;">{format_price(min_price)}</h3>
                        <p style="margin: 5px 0 0 0;">Best Price</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col4:
                platforms = set(p['platform'] for p in products)
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin: 0; color: #9b59b6;">{len(platforms)}</h3>
                    <p style="margin: 5px 0 0 0;">Platforms</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Sorting options
            sort_col1, sort_col2 = st.columns([1, 3])
            
            with sort_col1:
                sort_option = st.selectbox(
                    "Sort by:",
                    ["Price (Low to High)", "Price (High to Low)", "Platform", "Name"]
                )
            
            # Sort products based on selection
            if sort_option == "Price (Low to High)":
                products = sorted(products, key=lambda x: x['price'])
            elif sort_option == "Price (High to Low)":
                products = sorted(products, key=lambda x: x['price'], reverse=True)
            elif sort_option == "Platform":
                products = sorted(products, key=lambda x: x['platform'])
            elif sort_option == "Name":
                products = sorted(products, key=lambda x: x['name'])
            
            # Display products
            st.markdown(f"### 🛍️ Search Results ({len(products)} shown)")
            
            for i, product in enumerate(products):
                create_enhanced_product_card(product, i)
                
                if i < len(products) - 1:  # Don't add divider after last product
                    st.markdown("---")
        
        else:
            st.warning(f"No products found for '{search_query}' with the selected filters.")
            st.markdown("""
            ### 💡 Search Tips:
            - Try different keywords or spellings
            - Remove or adjust price filters
            - Search for broader terms (e.g., "phone" instead of specific model)
            - Check different platforms
            """)
    
    else:
        # Welcome screen with featured products
        st.markdown("### 🔥 Featured Products")
        
        # Show recent products as featured
        recent_products = fetch_recent_products(6)
        if recent_products:
            # Create a grid of featured products
            for i in range(0, len(recent_products), 2):
                col1, col2 = st.columns(2)
                
                with col1:
                    if i < len(recent_products):
                        create_enhanced_product_card(recent_products[i], f"featured_{i}")
                
                with col2:
                    if i + 1 < len(recent_products):
                        create_enhanced_product_card(recent_products[i + 1], f"featured_{i+1}")
        
        # Platform introduction
        st.markdown("---")
        st.markdown("""
        ### 🚀 Why Choose PriceDragon?
        
        - **🔍 Smart Search**: AI-powered product matching across platforms
        - **💰 Best Prices**: Compare prices from Taiwan's top e-commerce sites
        - **📈 Price Tracking**: Monitor price history and get alerts
        - **⚡ Real-time Data**: Always up-to-date product information
        - **🛡️ Trusted Results**: Verified product data and authentic reviews
        """)

def main():
    # Initialize session state
    if 'comparison_list' not in st.session_state:
        st.session_state.comparison_list = []
    
    # Sidebar navigation
    st.sidebar.markdown("## 🐉 Navigation")
    
    # Navigation tabs
    nav_options = [
        "🏠 Home & Search",
        "🔍 Smart Compare", 
        "🚨 Price Alerts",
        "📊 Market Analytics"
    ]
    
    selected_tab = st.sidebar.radio("", nav_options, label_visibility="collapsed")
    
    # Sidebar stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Platform Stats")
    
    try:
        recent_products = fetch_recent_products(100)
        if recent_products:
            df = pd.DataFrame(recent_products)
            platform_counts = df['platform'].value_counts()
            
            for platform, count in platform_counts.items():
                st.sidebar.metric(platform.upper(), f"{count:,}")
            
            # Additional stats
            total_value = df['price'].sum()
            st.sidebar.metric("Total Value", f"NT${total_value:,.0f}")
            
            avg_price = df['price'].mean()
            st.sidebar.metric("Avg Price", f"NT${avg_price:,.0f}")
    except:
        st.sidebar.info("Stats loading...")
    
    # Comparison sidebar
    if st.session_state.comparison_list:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔄 Comparison List")
        
        for i, product in enumerate(st.session_state.comparison_list):
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.sidebar.write(f"{product['name'][:30]}...")
            with col2:
                if st.sidebar.button("❌", key=f"remove_{i}"):
                    st.session_state.comparison_list.pop(i)
                    st.rerun()
        
        if st.sidebar.button("📊 Compare All"):
            st.session_state.show_comparison = True
    
    # Main content based on navigation
    if selected_tab == "🏠 Home & Search":
        render_main_search_page()
    
    elif selected_tab == "🔍 Smart Compare":
        render_product_comparison_page()
    
    elif selected_tab == "🚨 Price Alerts":
        render_price_alerts_page()
    
    elif selected_tab == "📊 Market Analytics":
        render_analytics_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; padding: 20px;">
        <p>🐉 PriceDragon - Powered by Advanced Web Scraping & AI Matching</p>
        <p>Comparing prices across Taiwan's major e-commerce platforms</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
