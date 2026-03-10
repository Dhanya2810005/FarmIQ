# 🌾 AgriChain Solutions - Procurement & Strategy Engine

**Source:** Ministry of Agriculture & Farmers Welfare (DA&FW) · Agmarknet · IMD · APEDA  
**Coverage:** All-India · 2021–25 Production · 268 Markets · 16 States · 641 Districts  
**Tools:** SQLite · Python (Pandas, Numpy, Matplotlib, SciPy) · Streamlit

---

## Executive Summary (SCR Framework)

### Situation
India's agricultural sector supports millions of livelihoods but operates with significant inefficiencies. Agri-businesses, FMCG companies, and policymakers struggle to optimize their supply chains, make data-driven procurement decisions, and target capital expenditures effectively due to fragmented and siloed data across production, weather, and commodity markets.

### Complication
The sector is currently facing three compounding structural risks that threaten profitability and sustainability:
1. **Sourcing Risk & Yield Volatility:** Output growth is often driven by unsustainable land expansion rather than yield efficiency, exposing supply chains to severe climate-induced shocks.
2. **Margin Erosion via Market Fragmentation:** Extreme price variations across 268+ mandis (markets) transfer immense value away from producers and buyers to intermediaries, destroying net-margin arbitrage opportunities.
3. **Suboptimal Capital Allocation:** Export concentration in low-value raw commodities ignores the massive upside and higher ROI achievable through targeted processing infrastructure (CAPEX) investments.

### Resolution
The **AgriChain Solutions Engine** is an enterprise-grade analytics platform that synthesizes millions of data points across crop production, daily market prices, rainfall correlations, and export trends. By leveraging advanced SQL (Window Functions, CTEs, LAG/LEAD) and predictive analytics, the engine provides actionable intelligence to:
- **Optimize Procurement:** Identify high-yield, low-volatility sourcing regions.
- **Maximize Arbitrage:** Calculate net-margin opportunities accounting for transport and spoilage.
- **Mitigate Climate Risk:** Forecast supply shocks using historical rainfall-deficit correlations.
- **Target Investments:** Direct capital expenditure towards high-growth processed commodity value chains.

---

## Project Architecture

```
agricultural-intelligence-india/
│
├── section_1.py                          ← Module 1: Crop Production Intelligence
├── mandi_intelligence.py                 ← Module 2: Market Price Intelligence
├── rainfall_climate_intelligence.py      ← Module 3: Rainfall & Climate Intelligence
├── module4_export_intelligence.py        ← Module 4: Agricultural Export Intelligence
├── module5_synthesis_intelligence.py     ← Module 5: Cross-Module Risk Synthesis ★
├── module3_rainfall_yield_correlation.py ← Module 3 Patch: Inferential Correlation ★
└── executive_summary_generator.py        ← Full-Project Executive Summary ★
```
★ = Added in v2.0 to address analytical depth gaps

---

## Datasets

| # | Dataset | Source | Key Fields |
|---|---------|--------|------------|
| 1 | Crop Area, Production & Yield | DA&FW | Crop, Season, Area/Prod/Yield (2021–25) |
| 2 | Mandi Price Data | Agmarknet (19 May 2025) | Commodity, Market, State, Modal/Min/Max Price |
| 3 | District Rainfall Normals | IMD | State, District, Monthly mm, Annual, Jun-Sep |
| 4 | Agricultural Export Data | APEDA / TradeStat | HS Code, Commodity, Export Value Cr, Growth % |

> **Data Quality Note:** Mandi data is a single-day snapshot. All market-based recommendations should be treated as directional until 30-90 day price history is available.

---

## Module Descriptions

### Module 1 — Crop Production Intelligence
**Central question:** Is India's agricultural output growth yield-driven or land-driven?

| Analysis | SQL Technique | Key Finding |
|----------|--------------|-------------|
| Production vs Area Growth | Window RANK, CASE classification | Maize = strongest dual-driver (+21% area, +28.7% production) |
| Crop Expansion Analysis | CTE + RANK, area trend | Gram contracted -15% — pulse policy risk |
| Yield Efficiency vs Area Share | CROSS JOIN totals, efficiency matrix | Cotton: large area, lowest yield — land misallocation |
| Seasonal Yield Advantage | PARTITION BY season | Heatmap shows Rabi advantage for Wheat/Gram |
| Yield Volatility (Climate Proxy) | Manual StdDev in SQL, CV% | Cotton and Bajra show highest yield volatility |
| Production Contribution | Cumulative SUM() OVER, Pareto | Sugarcane + Rice = majority of biomass output |
| Yield Ranking & Rank Shifts | NTILE, RANK, bump chart | Maize improved 3 rank positions in 4 years |
| Area-Yield Tradeoff Matrix | 2×2 quadrant via CROSS JOIN median | 4 crops in "Inefficient" quadrant — actionable |

---

### Module 2 — Market (Mandi) Intelligence
**Central question:** Where is value being lost between farm gate and consumer?

| Analysis | SQL Technique | Key Finding |
|----------|--------------|-------------|
| Price Fragmentation | CoV% classification, RANK() | Multiple commodities show 40%+ CoV = severely fragmented |
| Best Mandi per Commodity | PARTITION BY RANK on price | Location premium of up to 60% above national average |
| Best District per Commodity | Multi-level aggregation CTE | Consistent district-level price hubs identified |
| State Price Leadership | Nested CTE + frequency count | Certain states dominate as price leaders across commodities |
| Premium Markets | Pct_Beats_Avg metric | Markets that consistently beat national average identified |

---

### Module 3 — Rainfall & Climate Intelligence
**Central question:** Which crops face structural climate risk, and how strong is the rainfall-yield relationship?

| Analysis | SQL/Stats Technique | Key Finding |
|----------|--------------------|----|
| Monthly Rainfall Distribution | SQL aggregation, seasonal analysis | Jun-Sep accounts for 70%+ of annual rainfall nationally |
| Monsoon Dependency Index | State-level normalisation | High-dependency states clustered in central/peninsular India |
| **Rainfall-Yield Correlation ★** | Pearson + Spearman, scipy.stats | Rice r ≈ +0.5 (significant); Wheat r ≈ near zero (irrigated) |
| Regression with CI bands | OLS via scipy.linregress | 95% confidence intervals show prediction uncertainty |

> ★ Added in Module 3 Patch. The correlation analysis converts descriptive rainfall statistics into inferential claims about climate dependency.

---

### Module 4 — Export Intelligence
**Central question:** Is India exporting raw commodities when it should be exporting processed goods?

| Analysis | SQL Technique | Key Finding |
|----------|--------------|-------------|
| Raw vs Processed Export Share | HS code range classification | Raw agriculture dominates; processed food is <25% of agri exports |
| Export Concentration Risk | Cumulative share, Pareto | Top 3 HS chapters = majority of agri export value |
| Export Competitiveness Matrix | 4-quadrant CASE classification | Spices/Tea: Emerging Champions. Cereals: stress signals |
| Processing Opportunity Score | Threshold-based scoring | 3 sectors scored HIGH opportunity for value-add investment |
| YoY Growth Ranking | Simple growth computation | 40%+ of agri sectors showed negative YoY growth in 2023-24 |

---

### Module 5 — Cross-Module Synthesis ★ (New in v2.0)
**Central question:** Which crops carry the highest combined risk, and which represent the best risk-adjusted opportunity?

**Methodology:**
- Computed 4 risk dimensions per crop (yield volatility, market fragmentation, climate dependency, export weakness)
- Min-max normalised each dimension to 0-100 scale
- Weighted composite: D1=30%, D2=30%, D3=25%, D4=15%
- Opportunity score = production growth × yield growth trajectory
- Strategic quadrant: Risk × Opportunity 2×2 matrix

**Key Charts:**
- `M5_01_composite_risk_scorecard.png` — Heatmap + bar chart, all 10 crops × 4 dimensions
- `M5_02_strategic_quadrant_matrix.png` — Risk-Opportunity scatter (the single most actionable chart)
- `M5_03_radar_risk_profiles.png` — Radar charts for top-risk + safest crops

---

## Running the Project

```bash
# Run in order (each module is standalone except Module 5 which benefits from prior context)
python section_1.py
python mandi_intelligence.py
python rainfall_climate_intelligence.py
python module4_export_intelligence.py
python module3_rainfall_yield_correlation.py   # Run after module 3
python module5_synthesis_intelligence.py       # Run last — synthesises all modules
python executive_summary_generator.py          # Final — generates executive summary
```

All charts are saved to: `./charts/`

---

## Key Findings

| # | Finding | Source Module | Business Implication |
|---|---------|--------------|---------------------|
| 1 | Maize is India's breakout crop (+21% area, +28.7% prod) | M1 | Priority for value chain investment |
| 2 | Gram area contracted -15% | M1 | Pulse self-sufficiency at risk |
| 3 | Price fragmentation: 30-60% premium gap across mandis | M2 | Real-time price information system needed |
| 4 | Rice shows significant positive rainfall-yield correlation | M3P | Climate insurance priority crop |
| 5 | Wheat yield is irrigation-buffered (r ≈ 0) | M3P | Water policy: focus on canal efficiency |
| 6 | Raw agri exports dominate; processed food <25% | M4 | Food processing FDI opportunity |
| 7 | Composite risk: Cotton and Bajra score highest overall | M5 | Structural intervention needed |
| 8 | Maize + Rice = "Low Risk, High Opportunity" quadrant | M5 | Best risk-adjusted investment targets |

---

## Limitations & What Would Improve the Analysis

| Limitation | Impact | Fix |
|-----------|--------|-----|
| Mandi data = 1 day | High — price recommendations unreliable | Add 90-day rolling price series |
| 4-year production history | Medium — CV% statistically fragile | Extend to 10+ years (ICRISAT data available) |
| No destination country in export data | Medium — can't assess buyer concentration | Add APEDA destination-wise export data |
| Rainfall = climatological normals, not annual actuals | Medium — masks year-to-year shock | Add annual state rainfall (1901-2023 IMD series) |
| No farm-gate vs MSP price comparison | High — core BA question unanswered | Add CACP MSP data and join with mandi prices |

---

## Technical Highlights

- **Manual StdDev in SQLite**: SQLite has no `STDDEV()` function. Module 1 and 5 compute population standard deviation using `SQRT(SUM((x-mean)^2)/n)` entirely in SQL — demonstrating constraint-aware technical execution.
- **Window functions throughout**: `RANK() OVER (PARTITION BY ...)`, `NTILE()`, running cumulative `SUM() OVER (ORDER BY ... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` — all used purposefully, not decoratively.
- **Cross-source data joins**: Module 3 and Module 5 join Rainfall (IMD), Crop Production (DA&FW), Mandi Prices (Agmarknet), and Export data (APEDA) with explicit state name normalisation.
- **Inferential statistics**: Module 3 Patch uses `scipy.stats.pearsonr` and `linregress` to compute Pearson r, p-values, OLS regression lines, and 95% confidence interval bands per crop.
- **Composite scoring framework**: Module 5 implements a normalised, weighted multi-criteria scoring system — the kind of framework used in real investment and policy prioritisation decisions.
