import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so_what import so_what, finding

st.set_page_config(page_title="Market Arbitrage", page_icon="📈", layout="wide")
st.title("📈 Market Arbitrage & Spreads")
st.markdown("Identify optimal selling & procurement locations using net-margin calculations.")

@st.cache_resource
def get_conn():
    return sqlite3.connect("agri_india.db", check_same_thread=False)
conn = get_conn()

# ─── Section 1: Net Margin Arbitrage ─────────────────────────────────────────
st.header("Top Net-Margin Arbitrage Opportunities")
st.markdown("""
Net Margin = (Local Modal Price - National Avg Price) - (5% Transport Cost) - (2% Spoilage Cost).
The table shows the *#1 Market* for each commodity.
""")

query = """
WITH ranked AS (
    SELECT mp.Commodity, mp.Market, mp.State, mp.Modal_Price,
        cs.avg_price AS National_Avg,
        ROUND(mp.Modal_Price - cs.avg_price, 0) AS Gross_Arbitrage_Rs,
        ROUND(cs.avg_price * 0.05, 0) AS Transport_Cost_Rs,
        ROUND(mp.Modal_Price * 0.02, 0) AS Spoilage_Cost_Rs,
        ROUND((mp.Modal_Price - cs.avg_price) - (cs.avg_price * 0.05) - (mp.Modal_Price * 0.02), 0) AS Net_Margin_Rs,
        RANK() OVER (PARTITION BY mp.Commodity ORDER BY (mp.Modal_Price - cs.avg_price - (cs.avg_price * 0.05) - (mp.Modal_Price * 0.02)) DESC) AS Margin_Rank
    FROM mandi_prices mp
    JOIN commodity_stats cs ON mp.Commodity = cs.Commodity
)
SELECT * FROM ranked WHERE Margin_Rank = 1 AND Net_Margin_Rs > 0 ORDER BY Net_Margin_Rs DESC LIMIT 20
"""

try:
    df_margin = pd.read_sql(query, conn)

    if not df_margin.empty:
        top_commodity  = df_margin.iloc[0]["Commodity"]
        top_market     = df_margin.iloc[0]["Market"]
        top_state      = df_margin.iloc[0]["State"]
        top_margin     = df_margin.iloc[0]["Net_Margin_Rs"]
        top_nat_avg    = df_margin.iloc[0]["National_Avg"]
        margin_pct     = (top_margin / top_nat_avg * 100) if top_nat_avg > 0 else 0
        n_opportunities = len(df_margin)

        # State frequency — which state dominates
        top_state_count = df_margin["State"].value_counts()
        dominant_state  = top_state_count.index[0]
        dominant_count  = top_state_count.iloc[0]

        so_what("Market Arbitrage", [
            finding(
                f"{top_commodity} at {top_market}, {top_state} offers the highest net margin of ₹{top_margin:,.0f}/quintal",
                f"At {margin_pct:.0f}% above the national average after costs, this market represents "
                f"a concrete procurement cost saving. A buyer purchasing 1,000 quintals here vs the "
                f"national average saves approximately ₹{top_margin * 1000 / 100000:.1f} lakh.",
                priority="oppt",
                metric=f"₹{top_margin:,.0f}/quintal",
                metric_label=f"Net margin at {top_market} vs national average"
            ),
            finding(
                f"{dominant_state} dominates {dominant_count}/{n_opportunities} best arbitrage markets",
                f"Concentrating procurement sourcing in {dominant_state} mandis offers the highest "
                f"price efficiency across multiple commodities. However, this also introduces "
                f"geographic concentration risk — a transport disruption or regional drought "
                f"affects multiple lines simultaneously.",
                priority="medium"
            ),
            finding(
                "⚠️ This analysis uses a single-day price snapshot (19 May 2025)",
                "Mandi prices fluctuate daily. These arbitrage opportunities should be validated "
                "with 30–90 day price history before committing to sourcing strategy changes. "
                "Use this as a directional guide, not an operational instruction.",
                priority="risk"
            ),
        ])

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.dataframe(df_margin[['Commodity', 'Market', 'State', 'Modal_Price', 'National_Avg', 'Net_Margin_Rs']], use_container_width=True)
    with col2:
        fig1 = px.bar(df_margin, x='Commodity', y='Net_Margin_Rs', color='State', text='Market',
                      title="Net Margin (₹) by Commodity and State")
        st.plotly_chart(fig1, use_container_width=True)

    # ─── Section 2: Price Spread Volatility ──────────────────────────────────
    st.subheader("Market Spread Volatility")
    query_vol = """
    SELECT Commodity, n_markets, min_price, max_price, avg_price, cov_pct, (max_price - min_price) as spread_rs
    FROM commodity_stats WHERE n_markets > 10 ORDER BY spread_rs DESC LIMIT 15
    """
    df_vol = pd.read_sql(query_vol, conn)

    if not df_vol.empty:
        worst_fragmentation = df_vol.iloc[0]
        frag_commodity = worst_fragmentation["Commodity"]
        frag_spread    = worst_fragmentation["spread_rs"]
        frag_avg       = worst_fragmentation["avg_price"]
        frag_spread_pct = (frag_spread / frag_avg * 100) if frag_avg > 0 else 0

        so_what("Price Fragmentation", [
            finding(
                f"{frag_commodity} has the widest price spread: ₹{frag_spread:,.0f} across markets ({frag_spread_pct:.0f}% of avg price)",
                f"A buyer sourcing {frag_commodity} from the lowest-priced mandi vs highest would pay "
                f"₹{frag_spread:,.0f}/quintal less. On a 500-quintal purchase that is ₹{frag_spread*500/100000:.1f} lakh. "
                f"This is not a market efficiency — it is a solvable information gap.",
                priority="oppt",
                metric=f"₹{frag_spread:,.0f}",
                metric_label=f"Max price spread for {frag_commodity}"
            ),
            finding(
                "High CoV% commodities carry hidden procurement cost risk",
                "Commodities with >30% CoV are unpredictable to budget for. Build in a contingency "
                "reserve of at least 1.5× the CoV% on your quarterly procurement cost estimates for these items.",
                priority="medium"
            ),
        ], collapsed=True)

    fig2 = px.scatter(df_vol, x="avg_price", y="spread_rs", size="n_markets", color="cov_pct", text="Commodity",
                      title="Average Price vs Price Spread (Circle size = Market Count)",
                      labels={"spread_rs": "Price Spread (Max - Min)", "avg_price": "National Average Price"})
    fig2.update_traces(textposition='top right')
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ─── Section 3: MSP Gap ───────────────────────────────────────────────────
    st.header("MSP vs. Market Price Gap Analysis")
    st.markdown("Highlights crops where national average market prices are significantly above or below the MSP.")

    query_msp = """
    SELECT cs.Commodity, ROUND(cs.avg_price, 0) AS Market_Avg_Price,
        msp.[2024-25-MSP] AS MSP_2425,
        ROUND(cs.avg_price - msp.[2024-25-MSP], 0) AS MSP_Gap_Rs,
        ROUND((cs.avg_price - msp.[2024-25-MSP]) * 100.0 / msp.[2024-25-MSP], 1) AS Gap_Pct
    FROM commodity_stats cs
    JOIN msp_data msp ON LOWER(cs.Commodity) = LOWER(msp.Crop_Norm)
    WHERE msp.[2024-25-MSP] > 0 ORDER BY Gap_Pct ASC
    """
    df_msp = pd.read_sql(query_msp, conn)

    if not df_msp.empty:
        below_msp = df_msp[df_msp["Gap_Pct"] < 0]
        above_msp = df_msp[df_msp["Gap_Pct"] > 0]

        so_what("MSP Policy Risk", [
            finding(
                f"{len(below_msp)} commodity(ies) trade BELOW their official MSP",
                f"Crops below MSP: {', '.join(below_msp['Commodity'].tolist()) if not below_msp.empty else 'none'}. "
                "When market prices fall below MSP, the government typically activates procurement support — "
                "which can tighten private market availability suddenly. "
                "Flag these for supply availability monitoring, especially near harvest season.",
                priority="risk" if not below_msp.empty else "low"
            ),
            finding(
                f"{len(above_msp)} commodity(ies) trade ABOVE MSP — market premium confirmed",
                "Above-MSP crops indicate genuine market demand exceeding government floor price. "
                "These are safer for long-term offtake contracts as price floors reduce downside risk.",
                priority="oppt" if not above_msp.empty else "low"
            ),
        ], collapsed=True)

        col3, col4 = st.columns([1, 1])
        with col3:
            st.dataframe(df_msp, use_container_width=True)
        with col4:
            df_msp['Color'] = df_msp['Gap_Pct'].apply(lambda x: '#d62728' if x < 0 else '#2ca02c')
            fig3 = px.bar(df_msp, x='Gap_Pct', y='Commodity', orientation='h',
                          title="Premium/Discount relative to MSP (%)",
                          color='Color', color_discrete_map="identity")
            fig3.add_vline(x=0, line_width=2, line_dash="dash", line_color="black")
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No matching commodities found between Market Prices and official MSP data.")

    st.divider()
    st.header("Macro Price Seasonality & Inflation (WPI)")
    st.markdown("Tracks Wholesale Price Index history from 2012 to present.")

    df_wpi = pd.read_sql("SELECT Commodity, Month_Year, WPI_Index FROM wpi_data", conn)
    if not df_wpi.empty:
        df_wpi['Date'] = pd.to_datetime(df_wpi['Month_Year'], format='%B-%Y', errors='coerce')
        df_wpi = df_wpi.dropna(subset=['Date']).sort_values('Date')
        wpi_commodities = sorted(df_wpi['Commodity'].unique().tolist())
        selected_wpi = st.multiselect("Select Commodities to track WPI Inflation:", wpi_commodities,
                                      default=wpi_commodities[:3] if len(wpi_commodities) >= 3 else wpi_commodities)
        if selected_wpi:
            df_filtered = df_wpi[df_wpi['Commodity'].isin(selected_wpi)]

            # Dynamic so_what based on WPI trend
            so_what("WPI Inflation Context", [
                finding(
                    "WPI trends since 2012 reveal structural inflation in agricultural commodities",
                    "Commodities with WPI consistently above 150 (50%+ cumulative inflation) have "
                    "eroded real procurement margins significantly. Contracts denominated in nominal "
                    "rupees without escalation clauses have effectively gotten cheaper for suppliers "
                    "year-over-year — build WPI-linked price escalation into multi-year supply agreements.",
                    priority="medium"
                ),
            ], collapsed=True)

            fig_wpi = px.line(df_filtered, x='Date', y='WPI_Index', color='Commodity',
                              title="WPI Timeseries (Base = 100)")
            st.plotly_chart(fig_wpi, use_container_width=True)

except Exception as e:
    st.error(f"Error loading market data: {e}")
