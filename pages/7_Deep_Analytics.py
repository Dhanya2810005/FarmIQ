import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Deep Analytics", page_icon="🔬", layout="wide")

st.title("🔬 Multivariate Yield Intelligence")
st.markdown(
    "**Rigorous statistical analysis:** OLS multivariate regression of crop yield on rainfall, "
    "area expansion, and time — with full diagnostic output. This goes beyond describing *what* "
    "happened to understanding *why* and *by how much*."
)

@st.cache_resource
def get_conn():
    return sqlite3.connect("agri_india.db", check_same_thread=False)

conn = get_conn()

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_data():
    # Yield + area from crop_state_yield (cross-sectional by state)
    df_yield = pd.read_sql(
        "SELECT State_Norm, Crop, Avg_Yield FROM crop_state_yield", conn
    )
    # Rainfall by state
    df_rain = pd.read_sql(
        "SELECT State_Norm, ANNUAL AS Annual_Rain_mm, Monsoon_mm, Monsoon_Pct FROM rain_state", conn
    )
    # National production trends (for time-series analysis)
    df_prod = pd.read_sql(
        """SELECT Crop, Season,
           Area_2122, Area_2223, Area_2324, Area_2425,
           Yield_2122, Yield_2223, Yield_2324, Yield_2425
           FROM crop_all WHERE Season = 'Total'""", conn
    )
    # Market price stats
    df_mkt = pd.read_sql(
        "SELECT Commodity, avg_price, cov_pct FROM commodity_stats", conn
    )
    return df_yield, df_rain, df_prod, df_mkt

df_yield, df_rain, df_prod, df_mkt = load_data()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: CROSS-SECTIONAL MULTIVARIATE REGRESSION (State Level)
# Yield_i = β0 + β1·Monsoon_i + β2·Annual_Rain_i + ε_i
# ═══════════════════════════════════════════════════════════════════════════════
st.header("Part 1 — Cross-Sectional Multivariate Regression")
st.markdown(
    "**Research question:** Holding other rainfall factors constant, what is the independent effect of "
    "monsoon intensity on crop yield across Indian states? "
    "**Model:** `Yield = β₀ + β₁·(Monsoon_mm) + β₂·(Annual_Rain_mm) + ε`"
)

try:
    import statsmodels.api as sm
    import statsmodels.stats.api as sms
    from statsmodels.stats.diagnostic import het_breuschpagan

    crops = sorted(df_yield["Crop"].dropna().unique().tolist())
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_crop = st.selectbox("Select crop for regression:", crops, key="mv_crop")
        log_transform = st.checkbox(
            "Log-transform yield (reduces right-skew)",
            value=False,
            help="Log transformation can improve OLS assumptions when yield is right-skewed."
        )

    # Merge state yield + rainfall
    df_merge = (df_yield[df_yield["Crop"] == selected_crop]
                .merge(df_rain, on="State_Norm", how="inner")
                .dropna(subset=["Avg_Yield", "Monsoon_mm", "Annual_Rain_mm"]))

    if len(df_merge) < 5:
        st.warning(f"Insufficient data points ({len(df_merge)}) for multivariate regression. Need ≥ 5 states.")
    else:
        y_raw = df_merge["Avg_Yield"].values
        y = np.log(y_raw + 1) if log_transform else y_raw
        X = sm.add_constant(df_merge[["Monsoon_mm", "Annual_Rain_mm"]].values)
        model = sm.OLS(y, X).fit()

        # ── Regression summary panel ──────────────────────────────────────────
        with col2:
            r2 = model.rsquared
            r2_adj = model.rsquared_adj
            f_stat = model.fvalue
            f_pval = model.f_pvalue
            n_obs = int(model.nobs)

            quality = "🟢 Strong" if r2 > 0.6 else ("🟡 Moderate" if r2 > 0.35 else "🔴 Weak")
            st.markdown(f"**Model fit quality: {quality}**")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("R²", f"{r2:.3f}", help="Proportion of yield variance explained by rainfall variables.")
            m2.metric("Adj. R²", f"{r2_adj:.3f}", help="R² penalised for number of predictors.")
            m3.metric("F-statistic", f"{f_stat:.2f}")
            m4.metric("F p-value", f"{'< 0.001' if f_pval < 0.001 else f'{f_pval:.3f}'}",
                      help="Probability the model explains nothing. < 0.05 = statistically significant.")

        # ── Coefficient table ─────────────────────────────────────────────────
        st.subheader("Regression Coefficients")
        coef_names = ["Intercept", "Monsoon_mm", "Annual_Rain_mm"]
        coef_df = pd.DataFrame({
            "Variable": coef_names,
            "Coefficient": model.params,
            "Std Error": model.bse,
            "t-statistic": model.tvalues,
            "p-value": model.pvalues,
            "95% CI Lower": model.conf_int()[:, 0],
            "95% CI Upper": model.conf_int()[:, 1],
        }).round(4)

        def color_pval(val):
            if val < 0.01:  return "background-color: #d4edda; color: #155724"
            elif val < 0.05: return "background-color: #fff3cd; color: #856404"
            else:            return "background-color: #f8d7da; color: #721c24"

        st.dataframe(
            coef_df.style.applymap(color_pval, subset=["p-value"]),
            use_container_width=True
        )
        st.caption("Green p < 0.01 (highly significant) · Amber p < 0.05 (significant) · Red p ≥ 0.05 (not significant)")

        # ── Business interpretation ───────────────────────────────────────────
        monsoon_coef = model.params[1]
        monsoon_pval = model.pvalues[1]
        annual_coef  = model.params[2]
        annual_pval  = model.pvalues[2]

        avg_yield_val = float(df_merge["Avg_Yield"].mean())
        avg_monsoon   = float(df_merge["Monsoon_mm"].mean())
        shock_100mm   = monsoon_coef * (-100)  # 100mm deficit
        shock_100_pct = (shock_100mm / avg_yield_val) * 100 if avg_yield_val > 0 else 0

        st.subheader("📊 Business Interpretation")
        interp_col1, interp_col2 = st.columns(2)

        with interp_col1:
            if monsoon_pval < 0.05:
                direction = "increases" if monsoon_coef > 0 else "decreases"
                st.success(
                    f"**Monsoon Rainfall (statistically significant, p={monsoon_pval:.3f}):**  \n"
                    f"Each additional 1mm of monsoon rainfall {direction} {selected_crop} yield "
                    f"by **{abs(monsoon_coef):.4f} T/Ha**, holding annual rainfall constant.  \n\n"
                    f"A 100mm monsoon deficit (≈{100/avg_monsoon*100:.0f}% of state average) "
                    f"implies a yield change of **{shock_100_pct:+.1f}%** — "
                    f"equivalent to **{shock_100mm:+.3f} T/Ha**."
                )
            else:
                st.warning(
                    f"**Monsoon Rainfall (NOT significant, p={monsoon_pval:.3f}):**  \n"
                    f"After controlling for total annual rainfall, monsoon timing does not "
                    f"independently predict {selected_crop} yield in this dataset.  \n\n"
                    f"**Procurement implication:** {selected_crop} supply risk is less driven by monsoon "
                    f"distribution and more by total water availability or irrigation access."
                )

        with interp_col2:
            if annual_pval < 0.05:
                direction2 = "increases" if annual_coef > 0 else "decreases"
                st.info(
                    f"**Annual Rainfall (statistically significant, p={annual_pval:.3f}):**  \n"
                    f"Each additional 1mm of annual rainfall {direction2} yield by "
                    f"**{abs(annual_coef):.4f} T/Ha**, controlling for monsoon intensity.  \n\n"
                    f"This suggests {selected_crop} production benefits from year-round water "
                    f"availability, not just monsoon concentration."
                )
            else:
                st.info(
                    f"**Annual Rainfall (NOT significant, p={annual_pval:.3f}):**  \n"
                    f"Total annual rainfall does not independently predict {selected_crop} yield "
                    f"once monsoon rainfall is controlled for.  \n\n"
                    f"**Implication:** Monitor Jun–Sep monsoon as the key climate variable for "
                    f"this crop; annual averages are a misleading proxy."
                )

        # ── Diagnostic plots ──────────────────────────────────────────────────
        st.subheader("Model Diagnostics")
        st.markdown(
            "Good regression requires four conditions: linearity, normality of residuals, "
            "homoskedasticity, and no severe outliers. These plots test all four."
        )

        y_pred = model.fittedvalues
        residuals = model.resid
        std_resid = residuals / residuals.std()

        fig_diag = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Fitted vs Actual (linearity check)",
                "Residuals vs Fitted (homoskedasticity)",
                "Residual Distribution (normality)",
                "Standardised Residuals (outliers)"
            ]
        )

        # 1. Fitted vs Actual
        fig_diag.add_trace(go.Scatter(
            x=y_pred, y=y, mode="markers",
            marker=dict(color="#2980B9", size=8, opacity=0.7),
            text=df_merge["State_Norm"], hovertemplate="%{text}<br>Fitted: %{x:.2f}<br>Actual: %{y:.2f}",
            name="States"
        ), row=1, col=1)
        min_v, max_v = min(y.min(), y_pred.min()), max(y.max(), y_pred.max())
        fig_diag.add_trace(go.Scatter(
            x=[min_v, max_v], y=[min_v, max_v], mode="lines",
            line=dict(color="red", dash="dash"), name="Perfect fit"
        ), row=1, col=1)

        # 2. Residuals vs Fitted
        fig_diag.add_trace(go.Scatter(
            x=y_pred, y=residuals, mode="markers",
            marker=dict(color="#27AE60", size=8, opacity=0.7), name="Residuals"
        ), row=1, col=2)
        fig_diag.add_hline(y=0, line_dash="dash", line_color="red", row=1, col=2)

        # 3. Residual histogram
        fig_diag.add_trace(go.Histogram(
            x=residuals, nbinsx=10,
            marker_color="#8E44AD", opacity=0.75, name="Residuals"
        ), row=2, col=1)

        # 4. Standardised residuals
        fig_diag.add_trace(go.Scatter(
            x=list(range(len(std_resid))), y=std_resid,
            mode="markers", marker=dict(color="#E67E22", size=8),
            text=df_merge["State_Norm"],
            hovertemplate="%{text}: %{y:.2f}σ", name="Std Residuals"
        ), row=2, col=2)
        fig_diag.add_hline(y=2,  line_dash="dot", line_color="red",   row=2, col=2)
        fig_diag.add_hline(y=-2, line_dash="dot", line_color="red",   row=2, col=2)

        fig_diag.update_layout(height=550, showlegend=False, title_text=f"{selected_crop} — OLS Regression Diagnostic Plots")
        st.plotly_chart(fig_diag, use_container_width=True)

        # ── Breusch-Pagan heteroskedasticity test ─────────────────────────────
        try:
            bp_stat, bp_pval, _, _ = het_breuschpagan(residuals, X)
            if bp_pval > 0.05:
                st.success(f"✅ Breusch-Pagan test: p = {bp_pval:.3f} — No significant heteroskedasticity detected. OLS standard errors are reliable.")
            else:
                st.warning(f"⚠️ Breusch-Pagan test: p = {bp_pval:.3f} — Heteroskedasticity present. Consider robust standard errors or log-transforming yield.")
        except Exception:
            pass

        # ── Shapiro-Wilk normality test ───────────────────────────────────────
        if len(residuals) >= 5:
            sw_stat, sw_pval = stats.shapiro(residuals)
            if sw_pval > 0.05:
                st.success(f"✅ Shapiro-Wilk normality test: p = {sw_pval:.3f} — Residuals are approximately normally distributed.")
            else:
                st.warning(f"⚠️ Shapiro-Wilk normality test: p = {sw_pval:.3f} — Residuals deviate from normality. Interpret p-values cautiously with small samples.")

        # ── Outlier identification ────────────────────────────────────────────
        outliers = df_merge[np.abs(std_resid) > 1.8].copy()
        outliers["Std_Residual"] = std_resid[np.abs(std_resid) > 1.8].values
        if not outliers.empty:
            st.markdown("**States with large residuals (|std. residual| > 1.8σ) — examine for data quality or structural differences:**")
            st.dataframe(
                outliers[["State_Norm", "Avg_Yield", "Monsoon_mm", "Annual_Rain_mm", "Std_Residual"]].round(3),
                use_container_width=True
            )

except ImportError:
    st.error("statsmodels not installed. Run: `pip install statsmodels --break-system-packages`")
except Exception as e:
    st.error(f"Regression error: {e}")
    st.exception(e)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: PANEL REGRESSION — ALL CROPS SUMMARY TABLE
# Rank crops by rainfall sensitivity (monsoon β coefficient, significant only)
# ═══════════════════════════════════════════════════════════════════════════════
st.header("Part 2 — Rainfall Sensitivity League Table (All Crops)")
st.markdown(
    "Runs the bivariate Monsoon → Yield OLS regression for **every crop** and ranks them by "
    "the size and significance of the monsoon coefficient. "
    "This directly answers: *'Which crops face the greatest climate procurement risk?'*"
)

try:
    import statsmodels.api as sm

    results_all = []
    for crop in df_yield["Crop"].dropna().unique():
        df_c = (df_yield[df_yield["Crop"] == crop]
                .merge(df_rain, on="State_Norm", how="inner")
                .dropna(subset=["Avg_Yield", "Monsoon_mm"]))
        if len(df_c) < 4:
            continue
        try:
            X_c = sm.add_constant(df_c["Monsoon_mm"].values)
            m_c = sm.OLS(df_c["Avg_Yield"].values, X_c).fit()
            avg_y = df_c["Avg_Yield"].mean()
            avg_m = df_c["Monsoon_mm"].mean()
            beta_monsoon = m_c.params[1] if len(m_c.params) > 1 else 0
            pval_monsoon = m_c.pvalues[1] if len(m_c.pvalues) > 1 else 1
            # Elasticity: % yield change per % monsoon change
            elasticity = (beta_monsoon * avg_m / avg_y) if avg_y > 0 else 0
            # Shock: yield impact of 20% monsoon deficit
            shock_20_pct = (beta_monsoon * (avg_m * -0.20) / avg_y) * 100 if avg_y > 0 else 0
            results_all.append({
                "Crop": crop,
                "n_states": len(df_c),
                "R²": round(m_c.rsquared, 3),
                "Monsoon_β": round(beta_monsoon, 4),
                "p_value": round(pval_monsoon, 4),
                "Significant": "✅" if pval_monsoon < 0.05 else "❌",
                "Elasticity": round(elasticity, 3),
                "Yield_Shock_20pct_Deficit_%": round(shock_20_pct, 1),
                "Avg_Yield_T_Ha": round(avg_y, 2),
            })
        except Exception:
            continue

    df_all_reg = (pd.DataFrame(results_all)
                  .sort_values("Yield_Shock_20pct_Deficit_%", ascending=True)
                  .reset_index(drop=True))

    # Highlight significant results
    def style_sig(row):
        if row["p_value"] < 0.05 and row["Yield_Shock_20pct_Deficit_%"] < -5:
            return ["background-color: #f8d7da"] * len(row)
        elif row["p_value"] < 0.05:
            return ["background-color: #d4edda"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_all_reg.style.apply(style_sig, axis=1)
                        .background_gradient(cmap="RdYlGn", subset=["Yield_Shock_20pct_Deficit_%"]),
        use_container_width=True
    )
    st.caption(
        "Red rows = statistically significant negative shock > 5%. "
        "Green rows = significant but lower impact. "
        "Elasticity = % yield change per 1% monsoon change."
    )

    # ── Forest plot of monsoon coefficients ──────────────────────────────────
    df_sig = df_all_reg[df_all_reg["p_value"] < 0.10].copy().sort_values("Monsoon_β")
    if not df_sig.empty:
        st.subheader("Monsoon Coefficient Forest Plot (Significant Crops Only)")
        st.markdown(
            "Each bar shows the direction and magnitude of monsoon rainfall's effect on yield. "
            "Positive = higher monsoon → higher yield (rain-fed crops). "
            "Negative = inverse relationship (irrigation-dependent crops)."
        )
        fig_forest = px.bar(
            df_sig, x="Monsoon_β", y="Crop", orientation="h",
            color="Monsoon_β", color_continuous_scale="RdBu",
            text="Monsoon_β",
            labels={"Monsoon_β": "Monsoon Rainfall Coefficient (T/Ha per mm)"},
            title="Monsoon → Yield Regression Coefficient by Crop (p < 0.10)"
        )
        fig_forest.add_vline(x=0, line_dash="dash", line_color="black")
        fig_forest.update_traces(texttemplate="%{text:.4f}", textposition="outside")
        fig_forest.update_layout(height=max(300, len(df_sig) * 40), coloraxis_showscale=False)
        st.plotly_chart(fig_forest, use_container_width=True)

except Exception as e:
    st.error(f"League table error: {e}")
    st.exception(e)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: PRICE–RISK MULTIVARIATE ANALYSIS
# Correlate price volatility (CoV%) with production volatility (CV%) across crops
# ═══════════════════════════════════════════════════════════════════════════════
st.header("Part 3 — Price Volatility vs Supply Volatility: Are They Linked?")
st.markdown(
    "**Hypothesis:** Crops with high production volatility should show higher price volatility "
    "if markets are integrating supply signals. If the correlation is weak, it implies "
    "structural market failures (hoarding, export controls, MSP distortion) are decoupling "
    "price from fundamentals — a key procurement risk insight."
)

try:
    # Compute production CV% from time-series
    prod_cv_rows = []
    for _, row in df_prod.iterrows():
        vals = pd.to_numeric(
            row[["Yield_2122","Yield_2223","Yield_2324","Yield_2425"]],
            errors="coerce"
        ).dropna().values
        if len(vals) >= 3:
            cv = (np.std(vals, ddof=1) / np.mean(vals) * 100) if np.mean(vals) > 0 else 0
            prod_cv_rows.append({"Crop": row["Crop"], "Production_CV_pct": round(cv, 2)})

    df_prod_cv = pd.DataFrame(prod_cv_rows)

    # Merge with market CoV%
    df_mkt_merge = df_mkt.copy()
    df_mkt_merge["Crop_Lower"] = df_mkt_merge["Commodity"].str.lower()
    df_prod_cv["Crop_Lower"] = df_prod_cv["Crop"].str.lower()

    df_joint = df_prod_cv.merge(df_mkt_merge, on="Crop_Lower", how="inner").dropna()

    if len(df_joint) >= 4:
        x_pv = df_joint["Production_CV_pct"].values
        y_pv = df_joint["cov_pct"].values
        slope_pv, intercept_pv, r_pv, p_pv, se_pv = stats.linregress(x_pv, y_pv)

        fig_pv = px.scatter(
            df_joint, x="Production_CV_pct", y="cov_pct",
            text="Crop", trendline="ols",
            labels={"Production_CV_pct": "Production Volatility — Yield CV% (Supply Side)",
                    "cov_pct": "Price Volatility — Price CoV% (Market Side)"},
            title="Supply Volatility vs Price Volatility: Are Markets Reflecting Fundamentals?"
        )
        fig_pv.update_traces(textposition="top center")
        st.plotly_chart(fig_pv, use_container_width=True)

        sig_label = "statistically significant" if p_pv < 0.05 else "NOT statistically significant"
        direction = "positive" if slope_pv > 0 else "negative"

        if r_pv**2 > 0.3 and p_pv < 0.05:
            st.success(
                f"**📈 Markets ARE partially integrating supply signals** (R² = {r_pv**2:.2f}, p = {p_pv:.3f})  \n"
                f"The {direction} correlation is {sig_label}. Production volatility explains "
                f"**{r_pv**2*100:.0f}%** of price volatility variation.  \n\n"
                f"**Procurement implication:** For volatile-supply crops, build in a "
                f"**{slope_pv:.1f}% price premium buffer** for every 1% increase in expected yield CV."
            )
        elif p_pv >= 0.05:
            st.warning(
                f"**⚠️ Markets are NOT reliably integrating supply fundamentals** (R² = {r_pv**2:.2f}, p = {p_pv:.3f})  \n"
                f"The correlation between production volatility and price volatility is {sig_label}.  \n\n"
                f"**Procurement implication:** Price volatility is driven by factors *other* than "
                f"supply — likely policy interventions (MSP floors, export bans), seasonal speculation, "
                f"or mandi infrastructure. Procurement hedging should focus on mandi selection and "
                f"contract timing, not production forecasting alone."
            )
        else:
            st.info(f"Weak relationship detected (R² = {r_pv**2:.2f}, p = {p_pv:.3f}). Directionally {direction} but inconclusive.")
    else:
        st.warning("Insufficient matched crops for price-risk regression.")

except Exception as e:
    st.error(f"Price-risk analysis error: {e}")
    st.exception(e)
