"""PriceDragon Dashboard - Enhanced Version"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Page configuration
st.set_page_config(
    page_title="🐉 PriceDragon",
    page_icon="🐉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .product-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        background-color: #f9f9f9;
    }
    .price-highlight {
        font-size: 24px;
        font-weight: bold;
        color: #e74c3c;
    }
    .platform-badge {
        background-color: #3498db;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# API base URL
API_BASE_URL = "http://localhost:8000"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_products(query: str, platform: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None) -> List[Dict]:
    """Fetch products from API with caching"""
    try:
        params = {"q": query}
        if platform:
            params["platform"] = platform
        if min_price is not None:
            params["min_price"] = str(min_price)  # Convert to string for API
        if max_price is not None:
            params["max_price"] = str(max_price)  # Convert to string for API
            
        response = requests.get(f"{API_BASE_URL}/products/search", params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("products", [])
        return []
    except Exception as e:
        st.error(f"API Error: {e}")
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

def format_price(price: float) -> str:
    """Format price with currency"""
    return f"NT${price:,.0f}"

def create_price_comparison_chart(products: List[Dict]) -> Optional[go.Figure]:
    """Create price comparison chart"""
    if not products:
        return None  # This is now correct with Optional[go.Figure]
    
    df = pd.DataFrame(products)
    fig = px.bar(
        df, 
        x='name', 
        y='price', 
        color='platform',
        title="Price Comparison Across Platforms",
        labels={'price': 'Price (NT$)', 'name': 'Product'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def main():
    # Header
    st.title("🐉 PriceDragon")
    st.markdown("### Taiwan E-Commerce Price Comparison Platform")
    
    # Sidebar filters
    st.sidebar.header("🔍 Search Filters")
    
    # Main search
    search_query = st.sidebar.text_input(
        "Search Products", 
        placeholder="e.g., iPhone, MacBook, Samsung..."
    )
    
    # Platform filter
    platforms = ["All", "pchome", "momo", "shopee", "yahoo", "ruten"]
    selected_platform = st.sidebar.selectbox("Platform", platforms)
    platform_filter: Optional[str] = None if selected_platform == "All" else selected_platform
    
    # Price range filter
    st.sidebar.subheader("Price Range (NT$)")
    price_range = st.sidebar.slider(
        "Select price range",
        min_value=0,
        max_value=100000,
        value=(0, 50000),
        step=1000
    )
    
    # Show products button
    search_clicked = st.sidebar.button("🔍 Search Products", type="primary")
    
    # Main content area
    if search_query and (search_clicked or search_query):
        
        # Fetch products - now with proper Optional types
        with st.spinner("Searching products..."):
            products = fetch_products(
                search_query, 
                platform_filter,  # This is now Optional[str]
                float(price_range[0]), 
                float(price_range[1])
            )
        
        if products:
            # Results summary
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.success(f"Found {len(products)} products matching '{search_query}'")
            with col2:
                avg_price = sum(p['price'] for p in products) / len(products)
                st.metric("Average Price", format_price(avg_price))
            with col3:
                min_price = min(p['price'] for p in products)
                st.metric("Best Price", format_price(min_price))
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["📋 Product List", "📊 Price Comparison", "📈 Analytics"])
            
            with tab1:
                # Product list with enhanced display
                for i, product in enumerate(products):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{product['name'][:60]}{'...' if len(product['name']) > 60 else ''}**")
                            st.markdown(f"<span class='platform-badge'>{product['platform'].upper()}</span>", unsafe_allow_html=True)
                            if product.get('brand'):
                                st.caption(f"Brand: {product['brand']}")
                        
                        with col2:
                            current_price = product['price']
                            original_price = product.get('original_price')
                            
                            st.markdown(f"<div class='price-highlight'>{format_price(current_price)}</div>", unsafe_allow_html=True)
                            
                            if original_price and original_price > current_price:
                                discount = (1 - current_price/original_price) * 100
                                st.success(f"{discount:.0f}% OFF")
                        
                        with col3:
                            availability = "✅ Available" if product['availability'] else "❌ Out of Stock"
                            st.write(availability)
                        
                        with col4:
                            if st.button("📈 History", key=f"history_{i}"):
                                st.session_state[f"show_history_{product['product_id']}"] = True
                            
                            st.markdown(f"[🔗 View Product]({product['url']})")
                        
                        # Show price history if requested
                        if st.session_state.get(f"show_history_{product['product_id']}", False):
                            with st.expander(f"Price History - {product['name'][:40]}...", expanded=True):
                                history = fetch_price_history(product['platform'], product['product_id'])
                                if history:
                                    df_history = pd.DataFrame(history)
                                    df_history['scraped_at'] = pd.to_datetime(df_history['scraped_at'])
                                    
                                    fig = px.line(
                                        df_history, 
                                        x='scraped_at', 
                                        y='price',
                                        title=f"Price History - {product['name'][:40]}...",
                                        labels={'scraped_at': 'Date', 'price': 'Price (NT$)'}
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("No price history available")
                        
                        st.divider()
            
            with tab2:
                # Price comparison chart
                st.subheader("📊 Price Comparison")
                
                if len(products) > 1:
                    chart = create_price_comparison_chart(products)
                    if chart:  # Now properly handles Optional[go.Figure]
                        st.plotly_chart(chart, use_container_width=True)
                    
                    # Best deals table
                    st.subheader("🏆 Best Deals")
                    df = pd.DataFrame(products)
                    best_deals = df.nsmallest(5, 'price')[['name', 'platform', 'price', 'availability']]
                    best_deals['price'] = best_deals['price'].apply(format_price)
                    st.dataframe(best_deals, use_container_width=True)
                else:
                    st.info("Need at least 2 products for comparison")
            
            with tab3:
                # Analytics dashboard
                st.subheader("📈 Search Analytics")
                
                df = pd.DataFrame(products)
                
                # Platform distribution
                col1, col2 = st.columns(2)
                with col1:
                    platform_counts = df['platform'].value_counts()
                    fig_platform = px.pie(
                        values=platform_counts.values, 
                        names=platform_counts.index,
                        title="Products by Platform"
                    )
                    st.plotly_chart(fig_platform, use_container_width=True)
                
                with col2:
                    # Price distribution
                    fig_price = px.histogram(
                        df, 
                        x='price', 
                        nbins=20,
                        title="Price Distribution"
                    )
                    st.plotly_chart(fig_price, use_container_width=True)
                
                # Summary statistics
                st.subheader("📊 Summary Statistics")
                stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                
                with stats_col1:
                    st.metric("Total Products", len(products))
                with stats_col2:
                    st.metric("Platforms", df['platform'].nunique())
                with stats_col3:
                    st.metric("Avg Price", format_price(df['price'].mean()))
                with stats_col4:
                    available_count = df['availability'].sum()
                    st.metric("Available", f"{available_count}/{len(products)}")
        
        else:
            st.warning(f"No products found for '{search_query}' with the selected filters.")
            st.info("Try adjusting your search terms or filters.")
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to PriceDragon! 🐉
        
        Your one-stop platform for comparing prices across Taiwan's major e-commerce platforms.
        
        ### How to use:
        1. **Enter a search term** in the sidebar (e.g., "iPhone", "MacBook")
        2. **Apply filters** for platform, price range, etc.
        3. **Click Search** to find products
        4. **Compare prices** across different platforms
        5. **View price history** to track trends
        
        ### Supported Platforms:
        - 🛒 PChome 24h
        - 🛍️ Momo (Coming Soon)
        - 🏪 Shopee (Coming Soon)
        - 📱 Yahoo Shopping (Coming Soon)
        """)
        
        # Show some sample recent products
        st.subheader("🔥 Recent Products")
        try:
            response = requests.get(f"{API_BASE_URL}/products/", params={"limit": 5})
            if response.status_code == 200:
                recent_products = response.json()
                if recent_products:
                    df_recent = pd.DataFrame(recent_products)
                    st.dataframe(
                        df_recent[['name', 'platform', 'price', 'brand']].head(),
                        use_container_width=True
                    )
        except:
            st.info("Unable to load recent products")

    # Sidebar stats
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Platform Stats")
    try:
        response = requests.get(f"{API_BASE_URL}/products/", params={"limit": 100})
        if response.status_code == 200:
            products = response.json()
            if products:
                df = pd.DataFrame(products)
                platform_counts = df['platform'].value_counts()
                
                for platform, count in platform_counts.items():
                    # Ensure platform is a string before calling upper()
                    platform_str = str(platform)
                    st.sidebar.metric(platform_str.upper(), count)
    except:
        st.sidebar.info("Stats unavailable")

if __name__ == "__main__":
    main()