"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   AGRICULTURAL INTELLIGENCE SYSTEM FOR INDIA                                ║
║   EXECUTIVE SUMMARY GENERATOR                                               ║
║   Generates a structured, print-ready summary of all module findings        ║
╚══════════════════════════════════════════════════════════════════════════════╝

PURPOSE
───────
Every module in this project produces strong analytical outputs. What was
missing was a single document that:
  1. States the overarching thesis of the project
  2. Summarises the 3 key findings from each module
  3. Flags data quality limitations with their impact
  4. Translates findings into 5 concrete actionable recommendations
  5. Identifies what additional data would most improve the analysis

This is the document a business stakeholder reads. The charts and SQL are
the evidence. This is the argument.

Produces: executive_summary_chart.png  (visual 1-page summary)
"""

import os, warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import textwrap
warnings.filterwarnings("ignore")

CHART_DIR = "../charts"
os.makedirs(CHART_DIR, exist_ok=True)

C = dict(
    green="#27AE60", teal="#1ABC9C",  blue="#2980B9",  red="#E74C3C",
    amber="#F39C12", purple="#8E44AD", dark="#2C3E50",  grey="#95A5A6",
    light="#ECF0F1", white="#FFFFFF",  lime="#2ECC71",  orange="#E67E22",
)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 1 — PROJECT THESIS (what was missing from Modules 1-4)        ║
# ╚══════════════════════════════════════════════════════════════════════════╝
PROJECT_THESIS = """
India's agricultural sector faces three compounding structural risks:
(1) yield growth that is partially masking unsustainable land expansion,
(2) extreme market fragmentation that transfers value from farmers to intermediaries,
and (3) export concentration in low-value raw commodities. This system quantifies
each risk dimension at crop level and identifies where intervention — through
policy, investment, or value chain redesign — delivers the highest return.
"""

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 2 — MODULE FINDINGS                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
MODULE_FINDINGS = {
    "MODULE 1\nCrop Production\nIntelligence": {
        "color": C["blue"],
        "findings": [
            "Maize is India's breakout crop — +21% area expansion AND\n"
            "+28.7% production growth, making it the strongest dual-driver\n"
            "performer among all major crops (2021-22 to 2024-25).",

            "Rice and Wheat production growth outpaced area expansion,\n"
            "confirming that yield-enhancing inputs (seeds, fertiliser)\n"
            "are working. Policymakers can reinforce this with targeted\n"
            "input subsidies.",

            "Gram (chickpea) area contracted -15% despite India being the\n"
            "world's largest producer. Pulse self-sufficiency is at risk\n"
            "without direct area-expansion incentives.",
        ]
    },
    "MODULE 2\nMarket\nIntelligence": {
        "color": C["green"],
        "findings": [
            "Price fragmentation (measured by CoV% across mandis) shows\n"
            "that a farmer selling in the wrong market can receive 30-60%\n"
            "less than the national modal price for the same commodity.",

            "State-level price leadership is concentrated — certain states\n"
            "consistently offer above-average prices across multiple crops,\n"
            "suggesting infrastructure and market depth advantages.",

            "LIMITATION: This module's mandi data is a single-day snapshot\n"
            "(19 May 2025). Recommendations require 30-90 day time-series\n"
            "to be operationally reliable for farmer decision-support.",
        ]
    },
    "MODULE 3\nRainfall & Climate\nIntelligence": {
        "color": C["teal"],
        "findings": [
            "Pearson correlation analysis (Module 3 Patch) shows that\n"
            "Rice and rain-fed Kharif crops have statistically significant\n"
            "positive rainfall-yield correlations at state level.",

            "Wheat, Gram and Rapeseed show near-zero or negative rainfall\n"
            "correlation — confirming irrigation-buffered production.\n"
            "Water policy for these crops should focus on canal efficiency,\n"
            "not monsoon management.",

            "India's average monsoon dependency (Jun-Sep / Annual rainfall)\n"
            "varies from 60% in coastal states to 90% in semi-arid zones.\n"
            "States with >80% monsoon dependency carry structural yield risk.",
        ]
    },
    "MODULE 4\nExport\nIntelligence": {
        "color": C["amber"],
        "findings": [
            "Raw agricultural exports (HS 1-14) dominate India's agri export\n"
            "basket. The raw-to-processed value-add gap represents a large\n"
            "unrealised revenue opportunity — exporting processed food\n"
            "instead of raw commodities could 2-3x export earnings per tonne.",

            "Export concentration risk: 2-3 commodity categories drive the\n"
            "majority of agricultural export value. Any market disruption\n"
            "(global price collapse, phytosanitary ban) creates outsized\n"
            "impact on India's agri trade balance.",

            "Emerging export sectors (HS 6-9: spices, flowers, vegetables)\n"
            "show strong YoY growth from a small base — highest return on\n"
            "investment for export market development.",
        ]
    },
    "MODULE 5\nCross-Module\nSynthesis": {
        "color": C["purple"],
        "findings": [
            "Composite Risk Score integrating all 4 dimensions reveals that\n"
            "the highest-risk crops combine high yield volatility, extreme\n"
            "price fragmentation, AND full monsoon dependency — triple\n"
            "exposure that requires coordinated policy response.",

            "Strategic Quadrant Analysis identifies 'Priority Investment'\n"
            "crops: low composite risk + high opportunity score. These are\n"
            "the best candidates for agri-value-chain investment, contract\n"
            "farming, or FPO (Farmer Producer Organisation) support.",

            "Crops in the 'Structural Concern' quadrant (high risk + low\n"
            "opportunity) cannot be fixed by market mechanisms alone —\n"
            "they require direct policy support: MSP enforcement, crop\n"
            "insurance, or substitution incentives.",
        ]
    },
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 3 — DATA QUALITY REGISTER (professional addition)            ║
# ╚══════════════════════════════════════════════════════════════════════════╝
DATA_QUALITY = [
    ("Mandi Price Data",
     "Single-day snapshot (19 May 2025)",
     "HIGH",
     "Price fragmentation conclusions are directional only. Need 30-90 day history."),
    ("Crop Production Data",
     "4 years only (2021-22 to 2024-25). 5th year (2025-26) is projected.",
     "MEDIUM",
     "CV% based on 4 data points is statistically fragile. Flag in presentations."),
    ("Export Data",
     "HS chapter-level only. No destination country or volume data.",
     "MEDIUM",
     "Cannot assess market concentration by buyer country. Limits trade risk analysis."),
    ("Rainfall Data",
     "Climatological normals (multi-year averages per district), not annual actuals.",
     "MEDIUM",
     "Correlation is cross-sectional, not time-series. Causal claims are limited."),
    ("State Name Matching",
     "Manual normalisation dictionary. Some states may be dropped silently.",
     "LOW",
     "Validate matched vs unmatched states before publishing to stakeholders."),
]

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 4 — ACTIONABLE RECOMMENDATIONS                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝
RECOMMENDATIONS = [
    ("R1 — IMMEDIATE",   C["red"],
     "Prioritise Maize Value Chain",
     "Maize shows the strongest dual-driver growth. Invest in cold-chain,\n"
     "processing infrastructure, and export certification to capture\n"
     "the value currently lost between farm gate and export."),

    ("R2 — SHORT-TERM",  C["amber"],
     "Deploy Mandi Price Information System",
     "Price fragmentation analysis shows farmers systematically undersell.\n"
     "A real-time mandi price comparison tool (SMS/app) covering top 3\n"
     "markets per commodity per district would have direct farmer income impact."),

    ("R3 — SHORT-TERM",  C["amber"],
     "Gram Area Recovery Programme",
     "India's pulse self-sufficiency depends on reversing Gram's -15%\n"
     "area decline. Targeted MSP premium for Gram in contracting states\n"
     "would be cost-effective given existing procurement infrastructure."),

    ("R4 — MEDIUM-TERM", C["blue"],
     "Processed Food Export Acceleration",
     "Raw-to-processed export gap analysis shows major unrealised value.\n"
     "FDI incentives for food processing clusters near high-production\n"
     "districts of top 5 crops would shift export basket composition."),

    ("R5 — STRUCTURAL",  C["purple"],
     "Climate-Resilient Crop Diversification",
     "Composite risk analysis identifies crops with >70% monsoon dependency\n"
     "AND high yield volatility. Crop diversification incentives toward\n"
     "lower-risk crops in climate-vulnerable districts would reduce\n"
     "aggregate agricultural GDP volatility."),
]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  BUILD VISUAL EXECUTIVE SUMMARY                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝
fig = plt.figure(figsize=(20, 26))
fig.patch.set_facecolor("#F4F6F8")
gs  = GridSpec(7, 2, figure=fig, hspace=0.55, wspace=0.4,
               height_ratios=[0.5, 2.5, 2.5, 2.5, 2.5, 2.5, 3])

# ── Header ────────────────────────────────────────────────────────────────────
ax_title = fig.add_subplot(gs[0, :])
ax_title.set_facecolor(C["dark"])
ax_title.set_xticks([]); ax_title.set_yticks([])
for sp in ax_title.spines.values(): sp.set_visible(False)
ax_title.text(0.5, 0.72, "AGRICULTURAL INTELLIGENCE SYSTEM — INDIA",
              ha="center", va="center", transform=ax_title.transAxes,
              fontsize=17, fontweight="bold", color="white")
ax_title.text(0.5, 0.25, "Executive Summary  ·  5-Module Cross-Sectional Analysis  ·  "
              "Source: DA&FW · Agmarknet · IMD · APEDA",
              ha="center", va="center", transform=ax_title.transAxes,
              fontsize=9, color=C["light"], alpha=0.9)

# ── Project Thesis ────────────────────────────────────────────────────────────
ax_thesis = fig.add_subplot(gs[1, :])
ax_thesis.set_facecolor("#EBF5FB")
ax_thesis.set_xticks([]); ax_thesis.set_yticks([])
for sp in ax_thesis.spines.values():
    sp.set_visible(True); sp.set_color(C["blue"]); sp.set_linewidth(2)
ax_thesis.text(0.015, 0.85, "PROJECT THESIS",
               transform=ax_thesis.transAxes, fontsize=9,
               fontweight="bold", color=C["blue"], va="top")
wrapped = "\n".join(textwrap.wrap(PROJECT_THESIS.strip(), width=145))
ax_thesis.text(0.015, 0.62, wrapped,
               transform=ax_thesis.transAxes, fontsize=8.5,
               color=C["dark"], va="top", linespacing=1.6)

# ── Module Findings (5 rows × 2 panels) ──────────────────────────────────────
module_items = list(MODULE_FINDINGS.items())
row_positions = [
    (2, 0), (2, 1),
    (3, 0), (3, 1),
    (4, 0),
]

for i, (module_name, data) in enumerate(module_items):
    if i >= len(row_positions):
        break
    row, col = row_positions[i]

    # Module 5 spans full width if it's in position 4
    colspan = 2 if i == 4 else 1
    ax_m = fig.add_subplot(gs[row, col] if colspan == 1 else gs[row, :])

    ax_m.set_facecolor("#FAFCFF")
    ax_m.set_xticks([]); ax_m.set_yticks([])
    for sp in ax_m.spines.values():
        sp.set_visible(True); sp.set_color(data["color"]); sp.set_linewidth(2.5)

    # Module header bar
    ax_m.axhspan(0.82, 1.0, color=data["color"], alpha=0.12)
    ax_m.text(0.015, 0.915, module_name.replace("\n", " — "),
              transform=ax_m.transAxes, fontsize=8.5,
              fontweight="bold", color=data["color"], va="center")

    y_pos = 0.73
    for j, finding in enumerate(data["findings"]):
        bullet_x = 0.015
        text_x   = 0.035
        ax_m.text(bullet_x, y_pos, "●",
                  transform=ax_m.transAxes, fontsize=8,
                  color=data["color"], va="top")
        wrapped_f = "\n".join(textwrap.wrap(finding, width=68 if colspan == 1 else 140))
        ax_m.text(text_x, y_pos, wrapped_f,
                  transform=ax_m.transAxes, fontsize=7.5,
                  color=C["dark"], va="top", linespacing=1.4)
        line_count = wrapped_f.count("\n") + 1
        y_pos -= (0.24 + (line_count - 1) * 0.04)

# ── Data Quality Register ─────────────────────────────────────────────────────
ax_dq = fig.add_subplot(gs[5, :])
ax_dq.set_facecolor("#FEF9E7")
ax_dq.set_xticks([]); ax_dq.set_yticks([])
for sp in ax_dq.spines.values():
    sp.set_visible(True); sp.set_color(C["amber"]); sp.set_linewidth(2)
ax_dq.text(0.015, 0.93, "⚠  DATA QUALITY REGISTER  (Limitations analysts must disclose to stakeholders)",
           transform=ax_dq.transAxes, fontsize=8.5,
           fontweight="bold", color=C["amber"], va="top")

col_width = 1.0 / len(DATA_QUALITY)
for j, (dataset, limitation, severity, impact) in enumerate(DATA_QUALITY):
    x_start = j * col_width + 0.01
    sev_color = C["red"] if severity == "HIGH" else C["amber"] if severity == "MEDIUM" else C["grey"]
    ax_dq.text(x_start + col_width/2, 0.76, dataset,
               transform=ax_dq.transAxes, fontsize=7.5,
               fontweight="bold", color=C["dark"], ha="center", va="top")
    ax_dq.text(x_start + col_width/2, 0.62, f"[{severity}]",
               transform=ax_dq.transAxes, fontsize=7.5,
               fontweight="bold", color=sev_color, ha="center", va="top")
    wrapped_lim = "\n".join(textwrap.wrap(limitation, width=26))
    ax_dq.text(x_start + col_width/2, 0.50, wrapped_lim,
               transform=ax_dq.transAxes, fontsize=6.8,
               color=C["dark"], ha="center", va="top", linespacing=1.3,
               style="italic")
    wrapped_imp = "\n".join(textwrap.wrap(impact, width=26))
    ax_dq.text(x_start + col_width/2, 0.22, wrapped_imp,
               transform=ax_dq.transAxes, fontsize=6.5,
               color=C["grey"], ha="center", va="top", linespacing=1.3)

# ── Recommendations ───────────────────────────────────────────────────────────
ax_rec = fig.add_subplot(gs[6, :])
ax_rec.set_facecolor("#FDFEFE")
ax_rec.set_xticks([]); ax_rec.set_yticks([])
for sp in ax_rec.spines.values():
    sp.set_visible(True); sp.set_color(C["green"]); sp.set_linewidth(2)
ax_rec.text(0.015, 0.97, "ACTIONABLE RECOMMENDATIONS",
            transform=ax_rec.transAxes, fontsize=9,
            fontweight="bold", color=C["green"], va="top")

rec_col_w = 1.0 / len(RECOMMENDATIONS)
for j, (timing, color, title, body) in enumerate(RECOMMENDATIONS):
    x_s = j * rec_col_w + 0.01
    ax_rec.text(x_s + rec_col_w/2, 0.88, timing,
                transform=ax_rec.transAxes, fontsize=7,
                fontweight="bold", color=color, ha="center", va="top")
    ax_rec.text(x_s + rec_col_w/2, 0.78, title,
                transform=ax_rec.transAxes, fontsize=7.8,
                fontweight="bold", color=C["dark"], ha="center", va="top")
    wrapped_body = "\n".join(textwrap.wrap(body, width=28))
    ax_rec.text(x_s + rec_col_w/2, 0.62, wrapped_body,
                transform=ax_rec.transAxes, fontsize=6.8,
                color=C["dark"], ha="center", va="top", linespacing=1.4)

    # Divider line between recs
    if j < len(RECOMMENDATIONS) - 1:
        ax_rec.axvline((j + 1) * rec_col_w, color=C["light"], lw=1.2, alpha=0.7)

plt.savefig(f"{CHART_DIR}/00_executive_summary_full.png",
            dpi=145, bbox_inches="tight")
plt.close()
print(f"✔  Executive Summary saved → 00_executive_summary_full.png")


# ── Also print the plain-text executive summary ────────────────────────────────
print("\n" + "═"*70)
print("  EXECUTIVE SUMMARY — PLAIN TEXT")
print("═"*70)

print("\nPROJECT THESIS")
print("─"*50)
print(textwrap.fill(PROJECT_THESIS.strip(), width=68))

for module_name, data in MODULE_FINDINGS.items():
    clean_name = module_name.replace("\n", " ")
    print(f"\n{clean_name}")
    print("─"*50)
    for j, finding in enumerate(data["findings"], 1):
        print(f"  {j}. {textwrap.fill(finding.strip(), width=65, subsequent_indent='     ')}")

print("\nDATA QUALITY LIMITATIONS")
print("─"*50)
for dataset, limitation, severity, impact in DATA_QUALITY:
    print(f"  [{severity}] {dataset}: {limitation}")
    print(f"         → {impact}\n")

print("\nRECOMMENDATIONS")
print("─"*50)
for timing, color, title, body in RECOMMENDATIONS:
    print(f"  {timing}: {title}")
    print(f"    {textwrap.fill(body.strip(), width=65, subsequent_indent='    ')}\n")

print("\n  ✅  EXECUTIVE SUMMARY COMPLETE")
