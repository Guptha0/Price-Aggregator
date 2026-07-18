import os
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Safe import of the generic spec-override engine
try:
    from matcher import match_products
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from matcher import match_products

# --- INITIAL SYSTEM CONFIGURATION ---
st.set_page_config(
    page_title="Universal Price Aggregator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 100+ PRE-POPULATED UNIVERSAL PLATFORM REGISTRY
GLOBAL_PLATFORMS = [
    "Amazon", "Flipkart", "Meesho", "Croma", "Myntra", "Ajio", "Nykaa", "TataCliq",
    "RelianceDigital", "JioMart", "Blinkit", "Zepto", "Swiggy", "Zomato", "BigBasket",
    "eBay", "Walmart", "BestBuy", "ASOS", "Sephora", "Target", "Macys", "Newegg",
    "BandH", "Adorama", "Wayfair", "Overstock", "Etsy", "Aliexpress", "Alibaba",
    "Temu", "Shein", "Zappos", "HomeDepot", "Lowes", "Costco", "SamsClub",
    "Walgreens", "CVS", "RiteAid", "Ulta", "Nike", "Adidas", "Puma", "Reebok",
    "UnderArmour", "Lululemon", "HandM", "Zara", "Forever21", "Boohoo", "NastyGal",
    "FashionNova", "Farfetch", "SSENSE", "MRPORTER", "Netaporter", "QVC", "HSN",
    "Woot", "Rakuten", "MercadoLibre", "Shopee", "Lazada", "Tokopedia", "Bukalapak",
    "Zalora", "Snapdeal", "ShopClues", "PaytmMall", "FirstCry", "Lenskart", "Purplle",
    "Sugar", "MakeMyTrip", "Cleartrip", "Yatra", "Goibibo", "Agoda", "Booking",
    "Expedia", "Hotels", "Airbnb", "Vrbo", "Decathlon", "Ikea", "Pepperfry",
    "UrbanLadder", "CrateAndBarrel", "PotteryBarn", "WestElm", "WilliamsSonoma",
    "SurLaTable", "BedBathAndBeyond", "Michaels", "Joann", "HobbyLobby", "Chewy",
    "Petco", "PetSmart", "GameStop", "MicroCenter", "Apple", "Samsung", "Dell",
    "HP", "Lenovo", "Asus", "Acer", "Sony", "Microsoft", "Nintendo", "PlayStation",
    "Xbox", "Steam", "EpicGames", "GOG", "HumbleBundle", "Origin", "Ubisoft", "EA", "Blizzard"
]

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "price_history.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            product_name TEXT,
            platform TEXT,
            target_url TEXT,
            current_price REAL,
            currency TEXT,
            availability_status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            product_name TEXT PRIMARY KEY,
            target_price REAL,
            created_at TEXT,
            last_alerted_price REAL
        )
    """)
    conn.commit()
    conn.close()

initialize_database()

# --- LIVE URL SCRAPER INTEGRATION ---
try:
    from core.scraper import scrape_url
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from core.scraper import scrape_url

# --- DATA PIPELINE LOADER ---
@st.cache_data(ttl=30)
def load_aggregated_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM price_logs ORDER BY timestamp DESC", conn)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

@st.cache_data(ttl=30)
def load_alerts():
    conn = sqlite3.connect(DB_PATH)
    alerts_df = pd.read_sql_query("SELECT * FROM price_alerts", conn)
    conn.close()
    return alerts_df

df_all = load_aggregated_data()
alerts_df = load_alerts()

if df_all.empty:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sample_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO price_logs (timestamp, product_name, platform, target_url, current_price, currency, availability_status)
        VALUES (?, 'Premium Wireless ANC Headphones', 'Amazon', 'https://amazon.in', 9999.00, '₹', 'In Stock')
    """, (sample_time,))
    conn.commit()
    conn.close()
    st.rerun()

# --- MAIN HEADLINE INTERFACE ---
st.title("🛡️ Universal Price Aggregator")
st.markdown("Track and unify pricing structures across **100+ global platforms** using resilient semantic data mapping.")

# --- AUTOMATED ALERTS NOTIFICATION BANNER ---
if not df_all.empty and not alerts_df.empty:
    latest_prices = df_all.sort_values('timestamp').groupby('product_name').last().reset_index()
    for _, alert_row in alerts_df.iterrows():
        p_name = alert_row['product_name']
        t_price = alert_row['target_price']
        match_prod = latest_prices[latest_prices['product_name'] == p_name]
        if not match_prod.empty:
            c_price = match_prod.iloc[0]['current_price']
            if c_price <= t_price:
                st.success(f"🚨 **ALERT TRIGGERED:** The tracked asset '{p_name}' has plummeted below threshold to **₹{c_price:,.2f}** (Target was ₹{t_price:,.2f})!")

st.markdown("---")

# --- SIDEBAR INTERACTIVE FILTERS ---
st.sidebar.header("🔍 Analytical Configuration")

# Deduplicate dynamic + hardcoded platforms for autocomplete
tracked_platforms_in_db = df_all['platform'].unique().tolist() if not df_all.empty else []
all_selectable_platforms = sorted(list(set(GLOBAL_PLATFORMS + tracked_platforms_in_db)))

selected_platforms = st.sidebar.multiselect(
    "Filter Tracked Web Platforms",
    options=all_selectable_platforms,
    default=[],
    help="Select from 100+ pre-registered platforms or leave blank to monitor all actively logged assets."
)

active_platform_pool = selected_platforms if selected_platforms else tracked_platforms_in_db

tracked_products = sorted(df_all['product_name'].unique().tolist()) if not df_all.empty else []
selected_base_item = st.sidebar.selectbox("Select Active Item Inventory Base", options=tracked_products)

matched_variants = []
if selected_base_item:
    for item_name in tracked_products:
        is_match, _, _ = match_products(selected_base_item, item_name)
        if is_match:
            matched_variants.append(item_name)

df_filtered = df_all[
    (df_all['product_name'].isin(matched_variants)) &
    (df_all['platform'].isin(active_platform_pool))
] if not df_all.empty else pd.DataFrame()

# --- HIGH-END TABBED UI ARCHITECTURE ---
tab1, tab2, tab3 = st.tabs([
    "📊 Cross-Platform Aggregator Matrix", 
    "📈 Historical Trend Intelligence", 
    "🛠️ Platform Engine Diagnostics"
])

with tab1:
    # --- MODULE 1: LIVE URL INGESTION ENGINE ---
    st.write("### 📥 Ingest New Product Node")
    with st.container(border=True):
        url_col, btn_col = st.columns([4, 1])
        with url_col:
            input_url = st.text_input(
                "Paste product page link from any supported platform:",
                placeholder="https://meesho.com/... or https://amazon.in/...",
                label_visibility="collapsed"
            )
        with btn_col:
            process_click = st.button("Fetch & Track Item", use_container_width=True, type="primary")

        if process_click and input_url:
            try:
                parsed_url = urllib.parse.urlparse(input_url)
                netloc = parsed_url.netloc.replace("www.", "")
                domain = netloc.split('.')[0].capitalize() if netloc else "Unknown Platform"
                
                with st.spinner(f"Querying advanced semantic metadata wrappers from {domain}..."):
                    scraped_node = scrape_url(input_url)
                    
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO price_logs (timestamp, product_name, platform, target_url, current_price, currency, availability_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (scraped_node["timestamp"], scraped_node["product_name"], scraped_node["platform"], 
                          scraped_node["target_url"], scraped_node["current_price"], scraped_node["currency"], scraped_node["availability_status"]))
                    conn.commit()
                    conn.close()
                    
                st.success(f"Successfully indexed target item from {domain} into the database history tracking pool!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Ingestion engine optimization fault: {str(e)}")

    st.markdown("---")

    if not df_filtered.empty:
        latest_points = df_filtered.sort_values('timestamp').groupby(['platform', 'product_name']).last().reset_index()
        
        absolute_low = df_filtered['current_price'].min()
        absolute_high = df_filtered['current_price'].max()
        active_lowest_row = latest_points.loc[latest_points['current_price'].idxmin()]
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("🔥 Cheapest Source Price", f"₹{active_lowest_row['current_price']:,.2f}", delta=f"via {active_lowest_row['platform']}")
        with m_col2:
            st.metric("📉 Record Historic Low", f"₹{absolute_low:,.2f}")
        with m_col3:
            st.metric("📈 Record Historic Peak", f"₹{absolute_high:,.2f}")
            
        st.markdown("---")

        st.write("### 🔔 Automated Threshold Trigger Configurator")
        existing_alert = alerts_df[alerts_df['product_name'] == selected_base_item]
        existing_alert_price = existing_alert.iloc[0]['target_price'] if not existing_alert.empty else None
        
        if existing_alert_price is not None:
            st.info(f"🎯 Active Notification Threshold Rule Set: Background orchestrator fires immediately when price falls below **₹{existing_alert_price:,.2f}**.")
        
        with st.container(border=True):
            a_col1, a_col2 = st.columns([3, 1])
            with a_col1:
                alert_price = st.number_input(
                    "Set Target Trigger Price (₹):", 
                    value=float(existing_alert_price) if existing_alert_price is not None else float(active_lowest_row['current_price'] * 0.9),
                    step=100.0
                )
            with a_col2:
                if st.button("Commit Alert Target", use_container_width=True, type="secondary"):
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("""
                        INSERT INTO price_alerts (product_name, target_price, created_at)
                        VALUES (?, ?, ?)
                        ON CONFLICT(product_name) DO UPDATE SET target_price=excluded.target_price, created_at=excluded.created_at
                    """, (selected_base_item, alert_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    conn.close()
                    st.success("Alert rule threshold permanently registered down the logging pipeline.")
                    st.cache_data.clear()
                    st.rerun()

        st.markdown("---")
        
        st.write("### 📊 Live Cross-Platform Comparison Matrix")
        matrix_df = latest_points[['platform', 'product_name', 'current_price', 'availability_status', 'target_url', 'timestamp']].copy()
        
        def apply_color_scale(val_col):
            is_lowest = val_col == val_col.min()
            return ['background-color: rgba(46, 125, 50, 0.4); font-weight: bold; color: white;' if match else '' for match in is_lowest]

        styled_table = matrix_df.style.apply(apply_color_scale, subset=['current_price']).format({'current_price': '₹{:,.2f}'})
        st.dataframe(styled_table, use_container_width=True, hide_index=True, column_config={"target_url": st.column_config.LinkColumn("Source Link")})
    else:
        st.info("System operational logic ready. Ingest a live product URL path above to begin generation routines.")

with tab2:
    st.write("### 📈 Comprehensive Cross-Site Historical Trend Trajectory")
    if not df_filtered.empty:
        st.line_chart(data=df_filtered, x="timestamp", y="current_price", color="platform", use_container_width=True)
        
        # Price Volatility Calculator
        st.write("#### 🌪️ Price Volatility Calculator")
        abs_low = df_filtered['current_price'].min()
        abs_high = df_filtered['current_price'].max()
        
        if abs_high > 0 and abs_high != abs_low:
            volatility_pct = ((abs_high - abs_low) / abs_high) * 100
            st.metric(label="Total Percentage Shift (Peak to Low)", value=f"{volatility_pct:.2f}%", delta=f"High: ₹{abs_high:,.2f} ➔ Low: ₹{abs_low:,.2f}", delta_color="inverse")
        else:
            st.info("Insufficient differential data to calculate volatility.")
    else:
        st.info("Awaiting data points for historical charting.")

with tab3:
    st.write("### 🛠️ Platform Engine Diagnostics")
    st.write("Monitor the real-time extraction health of actively indexed platforms.")
    if not df_all.empty:
        diag_data = []
        for plat in df_all['platform'].unique():
            plat_df = df_all[df_all['platform'] == plat].sort_values('timestamp', ascending=False)
            last_scrape = plat_df.iloc[0]
            
            # If price is 0.0 or product name indicates an error, flag it as warning
            if last_scrape['current_price'] <= 0.0 or "Error" in last_scrape['product_name']:
                health_status = "⚠️ WARNING: Extraction Fault (Likely Dynamic Rendering or Captcha)"
            else:
                health_status = "✅ ONLINE: Valid Payload"
                
            diag_data.append({
                "Platform": plat,
                "Health Status": health_status,
                "Last Successful Ping": last_scrape['timestamp'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(last_scrape['timestamp'], pd.Timestamp) else last_scrape['timestamp'],
                "Last Recorded Price": f"₹{last_scrape['current_price']:,.2f}"
            })
            
        diag_df = pd.DataFrame(diag_data)
        st.dataframe(diag_df, use_container_width=True, hide_index=True)
    else:
        st.info("No platforms currently indexed in the diagnostics registry.")
