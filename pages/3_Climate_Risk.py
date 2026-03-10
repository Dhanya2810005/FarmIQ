import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Climate Risk", page_icon="🌧️", layout="wide")

st.title("🌧️ Climate Risk & Drought Sensitivity")
st.markdown("Assess the correlation between annual rainfall and state-level crop yields to model drought shocks.")

@st.cache_resource
def get_conn():
    return sqlite3.connect("agri_india.db", check_same_thread=False)

conn = get_conn()

st.header("State-Level Yield vs Monsoon Dependency")

query_climate = """
SELECT 
    c.State_Norm, 
    c.Crop, 
    c.Avg_Yield, 
    r.ANNUAL, 
    r.Monsoon_mm, 
    r.Monsoon_Pct
FROM crop_state_yield c
JOIN rain_state r on c.State_Norm = r.State_Norm
"""

try:
    df_climate = pd.read_sql(query_climate, conn)
    
    crops = df_climate["Crop"].unique()
    selected_crop = st.selectbox("Select Crop to Analyze Sensitivity:", sorted(crops))
    
    df_sub = df_climate[df_climate["Crop"] == selected_crop].copy()
    
    if len(df_sub) >= 3:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig1 = px.scatter(df_sub, x="Monsoon_mm", y="Avg_Yield", text="State_Norm", 
                              trendline="ols", title=f"{selected_crop}: Monsoon Rainfall vs Yield",
                              labels={"Monsoon_mm": "Monsoon Rainfall (mm)", "Avg_Yield": "Average Yield (T/Ha)"})
            fig1.update_traces(textposition="top center")
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            st.markdown(f"**{selected_crop} Climate Diagnostics:**")
            avg_yield = df_sub["Avg_Yield"].mean()
            st.metric("National Avg Yield (for available states)", f"{avg_yield:.2f} T/Ha")
            
            st.metric("Pearson Correlation (Monsoon to Yield)", f"{correlation:.3f}")
            
            # Water Footprint reference dictionary (Synthetic averages in mm)
            water_footprint_mm = {
                'Rice': 1200, 'Sugarcane': 1500, 'Cotton': 800, 'Wheat': 400,
                'Tur': 350, 'Maize': 500, 'Soybean': 450, 'Groundnut': 500,
                'Rapeseed & Mustard': 300, 'Gram': 250, 'Bajra': 250, 'Jute & Mesta': 600
            }
            
            req_water = water_footprint_mm.get(selected_crop, 400) # Default 400
            st.metric("Est. Water Footprint Req.", f"{req_water} mm")
            
            # Robust regression using user-requested statsmodels
            import statsmodels.api as sm
            if len(df_sub) > 2:
                # OLS Regression using statsmodels
                X = df_sub["Monsoon_mm"]
                X = sm.add_constant(X)
                y = df_sub["Avg_Yield"]
                model = sm.OLS(y, X).fit()
                
                if 'Monsoon_mm' in model.params:
                    slope = model.params['Monsoon_mm']
                else:
                    slope = 0
                    
                avg_monsoon = df_sub["Monsoon_mm"].mean()
                deficit_20 = avg_monsoon * 0.20
                yield_loss = slope * deficit_20
                yield_loss_pct = (yield_loss / avg_yield) * 100 if avg_yield > 0 else 0
                
                st.metric("Predicted Yield Impact (20% Monsoon Deficit)", f"{yield_loss_pct:.1f}%")
                
                if yield_loss_pct < -5:
                    st.error("🚨 Highly sensitive to drought shocks.")
                elif yield_loss_pct > 5:
                    st.success("✅ Inverse relationship: Benefits from lower monsoon (or requires controlled irrigation).")
                else:
                    st.info("ℹ️ Minimal impact from 20% deficit.")
    else:
        st.warning(f"Not enough data points to plot correlation for {selected_crop}.")
        
    st.markdown("### Raw State Rainfall & Yield Data")
    st.dataframe(df_sub, use_container_width=True)

except Exception as e:
    st.error(f"Error loading climate intelligence data: {e}")
