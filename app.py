import streamlit as st
import os

st.set_page_config(
    page_title="AgriChain Solutions",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌾 AgriChain Solutions")
st.markdown("### Procurement & Strategy Engine")
st.markdown("""
Welcome to the AgriChain Solutions platform. This decision-engine synthesizes millions of data points across India's agricultural sector to provide actionable intelligence for supply chain procurement and capital expenditure strategy.

**Navigate through the modules on the left sidebar:**
- **🌾 Production Intelligence:** Analyze crop yields, sourcing risk, and area-driven vs yield-driven growth.
- **📈 Market Arbitrage:** Identify optimal selling locations using net-margin calculations.
- **🌧️ Climate Risk:** Evaluate the impact of monsoon deficits on crop yields for drought-shock forecasting.
- **🚢 Export Strategy:** Target capital expenditures based on raw vs processed export growth.
- **🎯 Dynamic Recommender:** Custom cross-domain queries to find the best crops for specific scenarios.

---
*Built with Streamlit, Python, and SQLite.*
""")

# Check if the database exists
db_path = "agri_india.db"
if not os.path.exists(db_path):
    st.error(f"Database not found at `{db_path}`. Please run `python data_engine.py` to initialize the database.")
else:
    st.success("Database connected successfully. All systems operational.")
