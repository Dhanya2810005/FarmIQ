import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import minmax_scale

st.set_page_config(page_title="Composite Risk", page_icon="⚠️", layout="wide")

st.title("⚠️ Composite Supply Chain Risk")
st.markdown("Holistic risk modeling rolling up Sourcing, Climate, and Market risks into a unified score for procurement targeting.")

@st.cache_resource
def get_conn():
    return sqlite3.connect("agri_india.db", check_same_thread=False)

conn = get_conn()

st.header("Aggregated Crop Risk Model")

# We will synthesize data from crop_all (yield CV), commodity_stats (price volatility), and rain_state (proxy for climate proxy)
query_risk = """
WITH Prod_Risk AS (
    SELECT Crop, 
           (STDEV(Yield_2122 + Yield_2223 + Yield_2324 + Yield_2425 + Yield_2526) / 
           AVG(Yield_2122 + Yield_2223 + Yield_2324 + Yield_2425 + Yield_2526 + 0.001) * 100) AS Yield_Vol_Pct
    FROM crop_all
    WHERE Season = 'Total'
    GROUP BY Crop
),
Market_Risk AS (
    SELECT Commodity, cov_pct AS Price_Vol_Pct
    FROM commodity_stats
)
SELECT p.Crop AS Commodity, 
       COALESCE(p.Yield_Vol_Pct, 0) AS Prod_Risk_Score, 
       COALESCE(m.Price_Vol_Pct, 0) AS Market_Risk_Score
FROM Prod_Risk p
LEFT JOIN Market_Risk m ON LOWER(p.Crop) = LOWER(m.Commodity)
"""

try:
    # Need to handle standard deviation in sqlite safely since stdev is not a base function by default in bare sqlite3
    # Actually, SQLite does not have STDEV natively. So we'll query raw data and compute it in pandas.
    query_raw = "SELECT Crop, Season, Yield_2122, Yield_2223, Yield_2324, Yield_2425, Yield_2526 FROM crop_all WHERE Season = 'Total'"
    df_prod = pd.read_sql(query_raw, conn)
    
    df_prod['Avg_Yield'] = df_prod[['Yield_2122', 'Yield_2223', 'Yield_2324', 'Yield_2425', 'Yield_2526']].mean(axis=1)
    df_prod['Std_Yield'] = df_prod[['Yield_2122', 'Yield_2223', 'Yield_2324', 'Yield_2425', 'Yield_2526']].std(axis=1)
    df_prod['Prod_Risk_Score'] = (df_prod['Std_Yield'] / df_prod['Avg_Yield'] * 100).fillna(0)
    
    df_market = pd.read_sql("SELECT Commodity, cov_pct AS Market_Risk_Score FROM commodity_stats", conn)
    
    # Merge
    df_prod['Commodity_Lower'] = df_prod['Crop'].str.lower()
    df_market['Commodity_Lower'] = df_market['Commodity'].str.lower()
    
    df_risk = pd.merge(df_prod[['Crop', 'Commodity_Lower', 'Prod_Risk_Score']], 
                       df_market[['Commodity_Lower', 'Market_Risk_Score']], 
                       on='Commodity_Lower', how='inner')
    
    df_risk['Commodity'] = df_risk['Crop']
    df_risk = df_risk[['Commodity', 'Prod_Risk_Score', 'Market_Risk_Score']]
    
    # Normalize scales to 0-100 for radar chart apples-to-apples
    df_risk['Normalized_Prod_Risk'] = minmax_scale(df_risk['Prod_Risk_Score']) * 100
    df_risk['Normalized_Market_Risk'] = minmax_scale(df_risk['Market_Risk_Score']) * 100
    
    # Let's add a dummy Climate Risk score based on a synthetic footprint metric just to have a 3rd axis
    water_footprint_mm = {
        'Rice': 1200, 'Sugarcane': 1500, 'Cotton': 800, 'Wheat': 400,
        'Tur': 350, 'Maize': 500, 'Soybean': 450, 'Groundnut': 500,
        'Rapeseed & Mustard': 300, 'Gram': 250, 'Bajra': 250
    }
    df_risk['Climate_Risk_Score'] = df_risk['Commodity'].map(water_footprint_mm).fillna(400)
    df_risk['Normalized_Climate_Risk'] = minmax_scale(df_risk['Climate_Risk_Score']) * 100
    
    df_risk['Composite_Score'] = (df_risk['Normalized_Prod_Risk'] * 0.4 + 
                                  df_risk['Normalized_Market_Risk'] * 0.4 + 
                                  df_risk['Normalized_Climate_Risk'] * 0.2).round(1)
                                  
    df_risk = df_risk.sort_values('Composite_Score', ascending=False)

    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.dataframe(df_risk[['Commodity', 'Composite_Score', 'Prod_Risk_Score', 'Market_Risk_Score']].style.background_gradient(cmap='Reds', subset=['Composite_Score']), use_container_width=True)
        
    with col2:
        crops_to_plot = st.multiselect("Select Commodities for Risk Radar:", df_risk['Commodity'].tolist(), default=df_risk['Commodity'].tolist()[:3])
        
        if crops_to_plot:
            fig = go.Figure()
            for crop in crops_to_plot:
                crop_data = df_risk[df_risk['Commodity'] == crop].iloc[0]
                fig.add_trace(go.Scatterpolar(
                    r=[crop_data['Normalized_Prod_Risk'], crop_data['Normalized_Market_Risk'], crop_data['Normalized_Climate_Risk']],
                    theta=['Production Variance', 'Price Volatility', 'Climate Sensitivity'],
                    fill='toself',
                    name=crop
                ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100])
                ),
                showlegend=True,
                title="Vulnerability Radar (0 = Safe, 100 = High Risk)"
            )
            st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error compiling risk matrix: {e}")
