import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Dynamic Recommender", page_icon="🎯", layout="wide")

st.title("🎯 Dynamic Crop Recommender")
st.markdown("Filter across our comprehensive database to identify the best crop for your specific scenario based on analytical constraints.")

@st.cache_resource
def get_conn():
    return sqlite3.connect("agri_india.db", check_same_thread=False)

conn = get_conn()

# --- Load Lookup Data ---
try:
    # We load seasons from crop_season, states from crop_state_yield
    df_seasons = pd.read_sql("SELECT DISTINCT Season FROM crop_season", conn)
    seasons = ["All"] + sorted(df_seasons["Season"].astype(str).tolist())
    
    df_states = pd.read_sql("SELECT DISTINCT State_Norm FROM crop_state_yield", conn)
    states = ["All"] + sorted(df_states["State_Norm"].dropna().tolist())
    
except Exception:
    seasons = ["All", "Autumn", "Kharif", "Rabi", "Summer", "Winter"]
    states = ["All", "ANDHRA PRADESH", "ASSAM", "BIHAR", "GUJARAT", "MAHARASHTRA", "PUNJAB", "UTTAR PRADESH"]


st.sidebar.header("Scenario Parameters")
selected_season = st.sidebar.selectbox("Farming Season", seasons)
selected_state = st.sidebar.selectbox("Region / State", states)

optimization_goal = st.sidebar.radio(
    "Optimization Goal",
    ["Maximize Yield", "Maximize Market Net Margin", "Minimize Sourcing Risk"]
)

st.subheader(f"Querying: [{selected_season}] season in [{selected_state}] to [{optimization_goal}]")

# --- Dynamic Query Construction ---
try:
    if optimization_goal == "Maximize Yield":
        st.markdown("This query finds the Top 10 crops with the highest recorded production yields given the season and state constraints.")
        # We need to join crop_season and crop_state_yield
        
        base_query = """
        SELECT csy.Crop, csy.State_Norm AS State, Round(csy.Avg_Yield, 2) AS State_Avg_Yield_T_Ha
        FROM crop_state_yield csy
        """
        
        conditions = []
        if selected_season != "All":
            # crop_season contains season level data. We join to filter by season.
            base_query += " JOIN crop_season c_seas ON csy.Crop = c_seas.Crop COLLATE NOCASE "
            conditions.append(f"c_seas.Season = '{selected_season}'")
            
        if selected_state != "All":
            conditions.append(f"csy.State_Norm = '{selected_state}'")
            
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
            
        base_query += " ORDER BY csy.Avg_Yield DESC LIMIT 10"
        
        df_result = pd.read_sql(base_query, conn)
        st.dataframe(df_result, use_container_width=True)
        if not df_result.empty:
            fig = px.bar(df_result, x='Crop', y='State_Avg_Yield_T_Ha', color='State', title="Top Crops by Yield")
            st.plotly_chart(fig)
            
    elif optimization_goal == "Maximize Market Net Margin":
        st.markdown("This query finds the Top 10 crops with the highest Market Arbitrage / Net Margin given the constraints.")
        # Join mandi_prices, commodity_stats, and potentially filter by state
        
        query = """
        WITH ranked AS (
            SELECT
                mp.Commodity, mp.Market, mp.State, mp.Modal_Price,
                cs.avg_price AS National_Avg,
                ROUND((mp.Modal_Price - cs.avg_price) - (cs.avg_price * 0.05) - (mp.Modal_Price * 0.02), 0) AS Net_Margin_Rs,
                RANK() OVER (PARTITION BY mp.Commodity ORDER BY (mp.Modal_Price - cs.avg_price - (cs.avg_price * 0.05) - (mp.Modal_Price * 0.02)) DESC) AS Margin_Rank
            FROM mandi_prices mp
            JOIN commodity_stats cs ON mp.Commodity = cs.Commodity
        """
        conditions = []
        if selected_state != "All":
            conditions.append(f"UPPER(mp.State) LIKE '%{selected_state}%'")
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += """
        )
        SELECT Commodity, Market, State, Modal_Price, National_Avg, Net_Margin_Rs 
        FROM ranked WHERE Margin_Rank = 1 AND Net_Margin_Rs > 0 ORDER BY Net_Margin_Rs DESC LIMIT 10
        """
        df_result = pd.read_sql(query, conn)
        st.dataframe(df_result, use_container_width=True)
        if not df_result.empty:
            fig = px.bar(df_result, x='Commodity', y='Net_Margin_Rs', text='Market', title="Top Crops by Net Margin")
            st.plotly_chart(fig)
            
    elif optimization_goal == "Minimize Sourcing Risk":
        st.markdown("This query finds the Top 10 crops with the lowest historical yield volatility (CV%) i.e. highest reliability.")
        
        query = """
        WITH yield_stats AS (
            SELECT Crop, 
                ROUND(SQRT(((Yield_2122 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)*(Yield_2122 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0) + (Yield_2223 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)*(Yield_2223 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0) + (Yield_2324 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)*(Yield_2324 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0) + (Yield_2425 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)*(Yield_2425 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)) / 4.0) / ((Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0) * 100, 2) AS CV_Pct
            FROM crop_major
            WHERE Yield_2122 IS NOT NULL
        )
        """
        
        # We need to link crops to seasons/states if selected
        select_clause = "SELECT y.Crop, y.CV_Pct"
        from_clause = " FROM yield_stats y"
        where_conditions = []
        
        if selected_season != "All":
            from_clause += " JOIN crop_season c_seas ON y.Crop = c_seas.Crop COLLATE NOCASE"
            where_conditions.append(f"c_seas.Season = '{selected_season}'")
            
        if selected_state != "All":
            from_clause += " JOIN crop_state_yield c_state ON y.Crop = c_state.Crop COLLATE NOCASE"
            where_conditions.append(f"c_state.State_Norm = '{selected_state}'")
            select_clause += ", c_state.State_Norm AS State"
            
        where_clause = ""
        if where_conditions:
            where_clause = " WHERE " + " AND ".join(where_conditions)
            
        full_query = query + select_clause + from_clause + where_clause + " ORDER BY y.CV_Pct ASC LIMIT 10"
        
        df_result = pd.read_sql(full_query, conn)
        st.dataframe(df_result, use_container_width=True)
        if not df_result.empty:
            fig = px.bar(df_result, x='Crop', y='CV_Pct', title="Top Reliable Crops (Lowest Volatility %)")
            st.plotly_chart(fig)

except Exception as e:
    st.error(f"Error querying database: {e}")
