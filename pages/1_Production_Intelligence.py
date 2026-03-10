import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so_what import so_what, finding

st.set_page_config(page_title="Production Intelligence", page_icon="🌾", layout="wide")
st.title("🌾 Crop Production Intelligence")
st.markdown("Analyze yield volatility and sourcing risk across key commodities.")

@st.cache_resource
def get_conn():
    return sqlite3.connect("agri_india.db", check_same_thread=False)
conn = get_conn()

# ─── Section 1: Sourcing Risk ─────────────────────────────────────────────────
st.header("Crop Sourcing Risk & Yield Volatility (4-Year Average)")
st.markdown("Evaluates crops based on 4-year yield CV%, highlighting volatile supply chains.")

query = """
WITH yield_stats AS (
    SELECT Crop, ROUND((Yield_2122 + Yield_2223 + Yield_2324 + Yield_2425) / 4.0, 0) AS Avg_Yield,
        ROUND(SQRT(((Yield_2122 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)*(Yield_2122 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0) + (Yield_2223 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)*(Yield_2223 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0) + (Yield_2324 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)*(Yield_2324 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0) + (Yield_2425 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)*(Yield_2425 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)) / 4.0) / ((Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0) * 100, 2) AS CV_Pct
    FROM crop_major WHERE Yield_2122 IS NOT NULL
)
SELECT *, ROUND(MIN(100, CV_Pct * 10), 0) AS Sourcing_Risk_Score,
    CASE WHEN CV_Pct > 5 THEN 'High Sourcing Risk' WHEN CV_Pct > 2 THEN 'Moderate Sourcing Risk' ELSE 'Low Sourcing Risk' END AS Sourcing_Risk_Category
FROM yield_stats ORDER BY CV_Pct DESC;
"""

try:
    df_risk = pd.read_sql(query, conn)

    # ── SO WHAT callout ───────────────────────────────────────────────────────
    if not df_risk.empty:
        high_risk_crops = df_risk[df_risk["Sourcing_Risk_Category"] == "High Sourcing Risk"]["Crop"].tolist()
        low_risk_crops  = df_risk[df_risk["Sourcing_Risk_Category"] == "Low Sourcing Risk"]["Crop"].tolist()
        top_volatile    = df_risk.iloc[0]["Crop"]
        top_cv          = df_risk.iloc[0]["CV_Pct"]

        so_what("Production Risk", [
            finding(
                f"{top_volatile} has the highest yield volatility at {top_cv:.1f}% CV",
                f"A {top_cv:.0f}% CV means supply could swing ±{top_cv:.0f}% season-to-season. "
                f"Do NOT rely on spot purchasing for {top_volatile} — lock in contract volumes 1 season ahead.",
                priority="risk",
                metric=f"±{top_cv:.0f}% supply swing",
                metric_label=f"Season-to-season for {top_volatile}"
            ),
            finding(
                f"{len(high_risk_crops)} crops carry High Sourcing Risk: {', '.join(high_risk_crops[:4])}",
                "These crops require buffer stock policies or forward contracts to avoid procurement disruption. "
                "Price them with a volatility premium when negotiating annual supply agreements.",
                priority="high"
            ),
            finding(
                f"Stable procurement base: {', '.join(low_risk_crops[:4])} show Low Sourcing Risk",
                "These crops are safe for spot purchasing or short-term contracts. "
                "Free up working capital by reducing buffer stock requirements for this group.",
                priority="low"
            ),
        ])

    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df_risk, use_container_width=True)
    with col2:
        fig = px.bar(df_risk, x='Crop', y='CV_Pct', color='Sourcing_Risk_Category',
                     title="Yield Volatility (CV%) by Crop",
                     color_discrete_map={
                         'High Sourcing Risk': '#d62728',
                         'Moderate Sourcing Risk': '#ff7f0e',
                         'Low Sourcing Risk': '#2ca02c'})
        st.plotly_chart(fig, use_container_width=True)

    # ─── Section 2: Growth Driver ─────────────────────────────────────────────
    st.subheader("Area-Driven vs Yield-Driven Growth")
    query_growth = """
    SELECT Crop,
        ROUND((Area_2425 - Area_2122) / Area_2122 * 100, 1) AS Area_Growth_Pct,
        ROUND((Prod_2425 - Prod_2122) / Prod_2122 * 100, 1) AS Prod_Growth_Pct,
        CASE
            WHEN ((Prod_2425 - Prod_2122) / Prod_2122 * 100 - (Area_2425 - Area_2122) / Area_2122 * 100) > 2 THEN 'Yield-Driven Growth'
            WHEN ((Area_2425 - Area_2122) / Area_2122 * 100) > 2 THEN 'Area-Driven Growth'
            ELSE 'Stagnant'
        END AS Growth_Driver
    FROM crop_major ORDER BY Prod_Growth_Pct DESC;
    """
    df_growth = pd.read_sql(query_growth, conn)

    # ── SO WHAT callout ───────────────────────────────────────────────────────
    if not df_growth.empty:
        yield_driven = df_growth[df_growth["Growth_Driver"] == "Yield-Driven Growth"]["Crop"].tolist()
        area_driven  = df_growth[df_growth["Growth_Driver"] == "Area-Driven Growth"]["Crop"].tolist()
        stagnant     = df_growth[df_growth["Growth_Driver"] == "Stagnant"]["Crop"].tolist()

        so_what("Growth Trajectory", [
            finding(
                f"Yield-driven crops ({', '.join(yield_driven[:3])}) are improving efficiency",
                "Yield-driven growth is sustainable — it comes from better seeds, inputs, and practices, "
                "not just land expansion. These crops have long-term supply growth potential without "
                "competing for additional arable land. Prioritise for long-term offtake agreements.",
                priority="oppt"
            ),
            finding(
                f"Area-driven crops ({', '.join(area_driven[:3]) if area_driven else 'none'}) are expanding on borrowed land",
                "Area expansion is finite and economically risky — it often comes at the cost of other crops. "
                "Production growth in this group may plateau or reverse as land competition increases. "
                "Treat near-term supply abundance with caution for forward contracting.",
                priority="medium"
            ),
            finding(
                f"Stagnant crops ({', '.join(stagnant[:3])}) show no meaningful improvement",
                "Stagnant production combined with growing demand = import pressure. "
                "If any of these are key inputs, begin diversifying sourcing to import channels now.",
                priority="high" if stagnant else "low"
            ),
        ], collapsed=True)

    fig_growth = px.scatter(df_growth, x="Area_Growth_Pct", y="Prod_Growth_Pct",
                            color="Growth_Driver", text="Crop",
                            title="Crop Growth Trajectory (2021-22 vs 2024-25)",
                            labels={"Area_Growth_Pct": "Area Growth (%)", "Prod_Growth_Pct": "Production Growth (%)"})
    fig_growth.update_traces(textposition='top center')
    fig_growth.add_shape(type="line",
                         x0=df_growth["Area_Growth_Pct"].min(), y0=df_growth["Area_Growth_Pct"].min(),
                         x1=df_growth["Area_Growth_Pct"].max(), y1=df_growth["Area_Growth_Pct"].max(),
                         line=dict(color="grey", dash="dot"))
    st.plotly_chart(fig_growth, use_container_width=True)

    st.divider()

    # ─── Section 3: State Heatmap ─────────────────────────────────────────────
    st.header("State-Wise Crop Yield Heatmap")
    st.markdown("Geographic concentration of yield efficiency (Tonnes per Hectare).")

    df_heat = pd.read_sql("SELECT State_Norm AS State, Crop, Avg_Yield FROM crop_state_yield", conn)
    if not df_heat.empty:
        heat_pivot = df_heat.pivot(index="Crop", columns="State", values="Avg_Yield").fillna(0)

        # ── SO WHAT callout ───────────────────────────────────────────────────
        # Find the highest-yield state per crop and flag concentration
        top_state_per_crop = df_heat.loc[df_heat.groupby("Crop")["Avg_Yield"].idxmax()]
        concentration_crops = top_state_per_crop[
            top_state_per_crop["Avg_Yield"] > df_heat.groupby("Crop")["Avg_Yield"].mean().reindex(top_state_per_crop["Crop"]).values * 2
        ]

        so_what("Geographic Concentration Risk", [
            finding(
                "High-yield states represent concentrated sourcing geography",
                "If your top-producing states face a simultaneous climate event (drought, flood), "
                "procurement disruption risk compounds. Map your current supplier base against "
                "this heatmap — if >60% of volume comes from one state, diversify proactively.",
                priority="risk"
            ),
            finding(
                "Yield gaps between states reveal arbitrage and investment targets",
                "States with yields 50%+ below the national leader have untapped productivity potential. "
                "Contract farming in lower-yield states can secure supply at lower land costs while "
                "improving farmer income — a viable ESG and supply diversification strategy.",
                priority="oppt"
            ),
        ], collapsed=True)

        fig_heat = px.imshow(heat_pivot,
                             labels=dict(x="State", y="Crop", color="Yield (T/Ha)"),
                             title="Crop Yield Heatmap Across Indian States",
                             color_continuous_scale="YlGnBu")
        fig_heat.update_xaxes(side="top")
        st.plotly_chart(fig_heat, use_container_width=True)

except Exception as e:
    st.error(f"Error loading production intelligence data: {e}")
