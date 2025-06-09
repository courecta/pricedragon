"""Enhanced dashboard components for PriceDragon"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

API_BASE_URL = "http://localhost:8000"

@st.cache_data(ttl=300)
def fetch_similar_products(product_id: int, threshold: float = 0.6) -> List[Dict]:
    """Fetch similar products from API"""
    try:
        params = {"threshold": threshold, "limit": 10}
        response = requests.get(f"{API_BASE_URL}/comparison/similar/{product_id}", params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_best_price(product_name: str) -> Dict:
    """Find best price for a product"""
    try:
        response = requests.get(f"{API_BASE_URL}/comparison/best-price/{product_name}")
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception:
        return {}

@st.cache_data(ttl=600)
def fetch_price_alerts(days: int = 7, threshold: float = 10.0) -> Dict:
    """Fetch price drop alerts"""
    try:
        params = {"days": days, "threshold_percent": threshold}
        response = requests.get(f"{API_BASE_URL}/comparison/price-alerts", params=params)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception:
        return {}

def create_price_comparison_table(products: List[Dict]) -> pd.DataFrame:
    """Create a comparison table for products"""
    if not products:
        return pd.DataFrame()
    
    df = pd.DataFrame(products)
    df['formatted_price'] = df['price'].apply(lambda x: f"NT${x:,.0f}")
    df['discount'] = ((df['original_price'] - df['price']) / df['original_price'] * 100).round(1)
    df['savings'] = df['original_price'] - df['price']
    
    return df[['name', 'platform', 'formatted_price', 'discount', 'availability', 'brand']]

def render_product_comparison_page():
    """Render the product comparison page"""
    st.header("🔍 Smart Product Comparison")
    st.markdown("Find the best deals across all platforms with AI-powered matching")
    
    # Input for product search
    col1, col2 = st.columns([3, 1])
    
    with col1:
        product_name = st.text_input(
            "Product Name", 
            placeholder="e.g., iPhone 13 Pro, MacBook Air M2",
            help="Enter a product name to find the best prices across all platforms"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        search_clicked = st.button("🔍 Find Best Price", type="primary")
    
    if product_name and search_clicked:
        with st.spinner("Searching for best prices..."):
            best_price_data = fetch_best_price(product_name)
        
        if best_price_data and best_price_data.get('products'):
            products = best_price_data['products']
            
            # Summary metrics
            st.success(f"Found {best_price_data['total_found']} matching products!")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Best Price", f"NT${best_price_data['best_price']:,.0f}")
            with col2:
                prices = [p['price'] for p in products if p['price']]
                if len(prices) > 1:
                    price_range = max(prices) - min(prices)
                    st.metric("Price Range", f"NT${price_range:,.0f}")
            with col3:
                avg_similarity = sum(p['similarity_score'] for p in products) / len(products)
                st.metric("Avg Match Score", f"{avg_similarity:.2f}")
            with col4:
                platforms = set(p['platform'] for p in products)
                st.metric("Platforms", len(platforms))
            
            # Interactive comparison table
            st.subheader("📊 Price Comparison Table")
            
            # Create comparison DataFrame
            df = pd.DataFrame(products)
            df['formatted_price'] = df['price'].apply(lambda x: f"NT${x:,.0f}")
            df['match_score'] = df['similarity_score'].apply(lambda x: f"{x:.2f}")
            
            # Sort by price
            df_display = df.sort_values('price')[
                ['name', 'platform', 'formatted_price', 'match_score', 'brand']
            ].reset_index(drop=True)
            
            # Highlight best price
            def highlight_best_price(row):
                if row.name == 0:  # First row (lowest price)
                    return ['background-color: #d4edda'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                df_display.style.apply(highlight_best_price, axis=1),
                use_container_width=True
            )
            
            # Price distribution chart
            st.subheader("📈 Price Distribution")
            fig = px.box(
                df, 
                x='platform', 
                y='price',
                title="Price Distribution by Platform",
                color='platform'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Product details
            st.subheader("🛍️ Product Details")
            for i, product in enumerate(products[:5]):  # Show top 5
                with st.expander(f"{product['platform'].upper()} - {product['name'][:50]}..."):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Product:** {product['name']}")
                        st.write(f"**Brand:** {product.get('brand', 'N/A')}")
                        st.write(f"**Match Score:** {product['similarity_score']:.3f}")
                    
                    with col2:
                        st.metric("Price", f"NT${product['price']:,.0f}")
                        if product.get('original_price') and product['original_price'] > product['price']:
                            discount = (1 - product['price']/product['original_price']) * 100
                            st.success(f"{discount:.1f}% OFF")
                    
                    with col3:
                        availability = "✅ Available" if product['availability'] else "❌ Out of Stock"
                        st.write(availability)
                        
                        if product.get('url'):
                            st.markdown(f"[🔗 View Product]({product['url']})")
        
        else:
            st.warning(f"No products found matching '{product_name}'. Try a different search term.")

def render_price_alerts_page():
    """Render the price alerts page"""
    st.header("🚨 Price Drop Alerts")
    st.markdown("Track significant price drops across all platforms")
    
    # Settings
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        days = st.selectbox("Time Period", [1, 3, 7, 14, 30], index=2)
    
    with col2:
        threshold = st.slider("Min. Price Drop %", 5.0, 50.0, 10.0, 5.0)
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Alerts", type="primary"):
            st.cache_data.clear()
    
    # Fetch alerts
    with st.spinner("Checking for price drops..."):
        alerts_data = fetch_price_alerts(days, threshold)
    
    if alerts_data and alerts_data.get('price_drops'):
        price_drops = alerts_data['price_drops']
        
        # Summary
        st.success(f"Found {alerts_data['alerts_found']} price drops ≥ {threshold}% in the last {days} days")
        
        # Metrics
        if price_drops:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_drop = sum(p['price_drop_percent'] for p in price_drops) / len(price_drops)
                st.metric("Avg Price Drop", f"{avg_drop:.1f}%")
            
            with col2:
                max_drop = max(p['price_drop_percent'] for p in price_drops)
                st.metric("Max Price Drop", f"{max_drop:.1f}%")
            
            with col3:
                total_savings = sum(p['savings'] for p in price_drops)
                st.metric("Total Savings", f"NT${total_savings:,.0f}")
            
            with col4:
                platforms = set(p['platform'] for p in price_drops)
                st.metric("Platforms", len(platforms))
            
            # Price drop chart
            st.subheader("📊 Price Drop Distribution")
            df_drops = pd.DataFrame(price_drops)
            
            fig = px.scatter(
                df_drops.head(20), 
                x='original_price', 
                y='current_price',
                size='price_drop_percent',
                color='platform',
                hover_data=['name', 'price_drop_percent', 'savings'],
                title="Price Drops (Original vs Current Price)",
                labels={'original_price': 'Original Price (NT$)', 'current_price': 'Current Price (NT$)'}
            )
            
            # Add diagonal line for reference
            max_price = max(df_drops['original_price'].max(), df_drops['current_price'].max())
            fig.add_trace(go.Scatter(
                x=[0, max_price], y=[0, max_price],
                mode='lines', name='No Change Line',
                line=dict(dash='dash', color='gray')
            ))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Alerts table
            st.subheader("🎯 Price Drop Alerts")
            
            for i, alert in enumerate(price_drops[:10]):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{alert['name'][:60]}{'...' if len(alert['name']) > 60 else ''}**")
                        st.caption(f"Platform: {alert['platform'].upper()}")
                    
                    with col2:
                        st.metric(
                            "Current Price", 
                            f"NT${alert['current_price']:,.0f}",
                            delta=f"-{alert['price_drop_percent']:.1f}%"
                        )
                    
                    with col3:
                        st.write(f"**Was:** NT${alert['original_price']:,.0f}")
                        st.success(f"**Save:** NT${alert['savings']:,.0f}")
                    
                    with col4:
                        st.write(f"**Updated:** {alert['updated_at'][:10]}")
                        if alert.get('url'):
                            st.markdown(f"[🔗 View Deal]({alert['url']})")
                    
                    st.divider()
    
    else:
        st.info(f"No significant price drops found in the last {days} days with ≥{threshold}% threshold.")
        st.markdown("""
        ### Tips for finding price drops:
        - Try a longer time period (14-30 days)
        - Lower the price drop threshold (5-10%)  
        - Check back regularly as prices change frequently
        """)

def render_analytics_dashboard():
    """Render advanced analytics dashboard"""
    st.header("📈 Market Analytics")
    st.markdown("Advanced insights into pricing trends and market data")
    
    # Fetch recent products for analysis
    try:
        response = requests.get(f"{API_BASE_URL}/products/", params={"limit": 200})
        if response.status_code == 200:
            products = response.json()
            
            if products:
                df = pd.DataFrame(products)
                
                # Market overview
                st.subheader("🏪 Market Overview")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Products", len(df))
                
                with col2:
                    st.metric("Active Platforms", df['platform'].nunique())
                
                with col3:
                    avg_price = df['price'].mean()
                    st.metric("Average Price", f"NT${avg_price:,.0f}")
                
                with col4:
                    available_pct = (df['availability'].sum() / len(df)) * 100
                    st.metric("Availability Rate", f"{available_pct:.1f}%")
                
                # Platform analysis
                st.subheader("🔍 Platform Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Platform distribution
                    platform_counts = df['platform'].value_counts()
                    fig_platform = px.pie(
                        values=platform_counts.values,
                        names=platform_counts.index,
                        title="Product Distribution by Platform"
                    )
                    st.plotly_chart(fig_platform, use_container_width=True)
                
                with col2:
                    # Price comparison by platform
                    fig_price = px.box(
                        df,
                        x='platform',
                        y='price',
                        title="Price Distribution by Platform"
                    )
                    st.plotly_chart(fig_price, use_container_width=True)
                
                # Brand analysis
                if 'brand' in df.columns and df['brand'].notna().any():
                    st.subheader("🏷️ Brand Analysis")
                    
                    # Top brands
                    brand_counts = df['brand'].value_counts().head(10)
                    if not brand_counts.empty:
                        fig_brands = px.bar(
                            x=brand_counts.values,
                            y=brand_counts.index,
                            orientation='h',
                            title="Top 10 Brands by Product Count"
                        )
                        fig_brands.update_layout(yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_brands, use_container_width=True)
                
                # Price trends
                st.subheader("💰 Price Analysis")
                
                # Price histogram
                fig_hist = px.histogram(
                    df,
                    x='price',
                    nbins=30,
                    title="Price Distribution",
                    labels={'price': 'Price (NT$)', 'count': 'Number of Products'}
                )
                st.plotly_chart(fig_hist, use_container_width=True)
                
                # Summary statistics
                st.subheader("📊 Statistical Summary")
                
                price_stats = df['price'].describe()
                
                stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                
                with stats_col1:
                    st.metric("Median Price", f"NT${price_stats['50%']:,.0f}")
                
                with stats_col2:
                    st.metric("Min Price", f"NT${price_stats['min']:,.0f}")
                
                with stats_col3:
                    st.metric("Max Price", f"NT${price_stats['max']:,.0f}")
                
                with stats_col4:
                    st.metric("Price Std Dev", f"NT${price_stats['std']:,.0f}")
            
            else:
                st.info("No product data available for analysis")
        
        else:
            st.error("Unable to fetch product data for analysis")
    
    except Exception as e:
        st.error(f"Error loading analytics data: {e}")
