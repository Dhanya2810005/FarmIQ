import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Export Strategy", page_icon="🚢", layout="wide")

st.title("🚢 CAPEX Investment Targeting")
st.markdown("Evaluates export sectors based on growth trajectory to recommend CAPEX processing infrastructure integration.")

@st.cache_resource
def get_conn():
    return sqlite3.connect("agri_india.db", check_same_thread=False)

conn = get_conn()

st.header("Raw vs Processed Export Growth & Strategy")

query_export = """
WITH categorised AS (
    SELECT HSCode, ShortName, Val_2223, Val_2324, Growth,
        CASE
            WHEN HSCode BETWEEN 1  AND 14 THEN 'Raw Agriculture'
            WHEN HSCode BETWEEN 15 AND 18 THEN 'Semi-Processed'
            WHEN HSCode BETWEEN 19 AND 24 THEN 'Processed Food'
            ELSE 'Other'
        END AS Category
    FROM exports
    WHERE HSCode BETWEEN 1 AND 24
)
SELECT ShortName AS Sector, Category, ROUND(Val_2324, 0) AS Export_Val_Cr, ROUND(Growth, 1) AS YoY_Growth_pct,
    CASE
        WHEN Category = 'Processed Food' AND Growth > 5 THEN 'PRIORITY CAPEX'
        WHEN Category = 'Semi-Processed' AND Growth > 0 THEN 'MODERATE CAPEX'
        WHEN Category = 'Raw Agriculture' AND Growth > 0 THEN 'RAW BOTTLENECK - NEEDS PROCESSING'
        ELSE 'MAINTAIN / NO CAPEX'
    END AS Capex_Strategy
FROM categorised
WHERE Category IN ('Raw Agriculture', 'Semi-Processed', 'Processed Food')
ORDER BY Export_Val_Cr DESC;
"""

try:
    df_capex = pd.read_sql(query_export, conn)
    
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.dataframe(df_capex, use_container_width=True)
    with col2:
        fig_capex = px.scatter(df_capex, x="Export_Val_Cr", y="YoY_Growth_pct", color="Capex_Strategy", text="Sector",
                          title="Export Volume vs Growth by Processing Strategy", log_x=True,
                          color_discrete_map={
                              'PRIORITY CAPEX': '#2ca02c',
                              'MODERATE CAPEX': '#ff7f0e',
                              'RAW BOTTLENECK - NEEDS PROCESSING': '#d62728',
                              'MAINTAIN / NO CAPEX': '#7f7f7f'
                          })
        fig_capex.update_traces(textposition='top center')
        st.plotly_chart(fig_capex, use_container_width=True)
        
        
    st.subheader("Commodity Value breakdown (2023-24)")
    fig_pie = px.pie(df_capex, values='Export_Val_Cr', names='Category', title="Export Share by Processing Level")
    st.plotly_chart(fig_pie, use_container_width=True)
except Exception as e:
    st.error(f"Error loading initial export data: {e}")

st.divider()

st.header("Export Competitiveness Matrix")
st.markdown("Classifies export sectors into quadrants based on value vs. YoY growth to determine market maturity.")

query_matrix = """
SELECT
    ShortName,
    HSCode,
    ROUND(Val_2324, 2) AS Val_2324_Cr,
    ROUND(Growth, 2)   AS YoY_Growth,
    CASE
        WHEN Val_2324 > (SELECT AVG(Val_2324) FROM exports WHERE HSCode BETWEEN 1 AND 24)
             AND Growth > 0 THEN 'Export Champions'
        WHEN Val_2324 > (SELECT AVG(Val_2324) FROM exports WHERE HSCode BETWEEN 1 AND 24)
             AND Growth <= 0 THEN 'Mature / Under Stress'
        WHEN Val_2324 <= (SELECT AVG(Val_2324) FROM exports WHERE HSCode BETWEEN 1 AND 24)
             AND Growth > 0 THEN 'Emerging Exports'
        ELSE 'Weak Sectors'
    END AS Quadrant
FROM exports
WHERE HSCode BETWEEN 1 AND 24
ORDER BY Val_2324 DESC;
"""
try:
    df_matrix = pd.read_sql(query_matrix, conn)
    colA, colB = st.columns([1, 1.2])
    with colA:
        st.dataframe(df_matrix, use_container_width=True)
    with colB:
        # Calculate average for the quadrant lines
        avg_val = max(1, df_matrix['Val_2324_Cr'].mean())
        
        fig_matrix = px.scatter(df_matrix, x="Val_2324_Cr", y="YoY_Growth", color="Quadrant", text="ShortName",
                                title="Export Competitiveness Quadrants", log_x=True)
        fig_matrix.add_hline(y=0, line_dash="dash", line_color="red")
        fig_matrix.add_vline(x=avg_val, line_dash="dash", line_color="blue")
        fig_matrix.update_traces(textposition='top right')
        st.plotly_chart(fig_matrix, use_container_width=True)
except Exception as e:
    st.warning(f"Competitiveness Matrix failed to load: {e}")

st.divider()

st.header("Export Concentration Risk")
st.markdown("Identifies the dependency on top agricultural commodities based on cumulative share thresholds.")

query_conc = """
WITH agri AS (
    SELECT HSCode, ShortName, Val_2223, Val_2324, Growth
    FROM exports
    WHERE HSCode BETWEEN 1 AND 24
),
totals AS (
    SELECT SUM(Val_2324) AS Grand_Total FROM agri
)
SELECT
    a.ShortName,
    a.HSCode,
    ROUND(a.Val_2324, 2) AS Val_2324_Cr,
    ROUND(100.0 * a.Val_2324 / t.Grand_Total, 2) AS Export_Share_pct,
    ROUND(SUM(100.0 * b.Val_2324 / t.Grand_Total), 2) AS Cumulative_Share_pct,
    a.Growth
FROM agri a
JOIN totals t
JOIN agri b ON b.Val_2324 >= a.Val_2324
GROUP BY a.HSCode
ORDER BY a.Val_2324 DESC LIMIT 15;
"""
try:
    df_conc = pd.read_sql(query_conc, conn)
    colC, colD = st.columns([1, 1])
    with colC:
        st.dataframe(df_conc, use_container_width=True)
    with colD:
        fig_pareto = px.bar(df_conc, x='ShortName', y='Val_2324_Cr', color='Growth', 
                            title="Top 15 Export Sectors by Value & Growth", height=400)
        st.plotly_chart(fig_pareto, use_container_width=True)
except Exception as e:
    st.warning("Concentration analysis failed to load.")
