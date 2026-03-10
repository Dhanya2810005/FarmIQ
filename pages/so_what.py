"""
so_what.py — Reusable "So What" callout utility for the AgriChain platform.

Usage in any Streamlit page:
    from so_what import so_what, finding

    so_what("Production Risk", [
        finding("Maize is outperforming", "Contract-farm Maize NOW before area peaks", "high"),
        finding("Gram is contracting", "Pulse imports will cost ₹3,200 Cr extra", "medium"),
    ])
"""
import streamlit as st

PRIORITY_COLORS = {
    "high":   {"bg": "#FFF3CD", "border": "#F0A500", "badge_bg": "#E67E22", "badge_text": "HIGH PRIORITY"},
    "medium": {"bg": "#D1ECF1", "border": "#17A2B8", "badge_bg": "#2980B9", "badge_text": "MEDIUM PRIORITY"},
    "low":    {"bg": "#D4EDDA", "border": "#28A745", "badge_bg": "#27AE60", "badge_text": "LOW PRIORITY"},
    "risk":   {"bg": "#F8D7DA", "border": "#DC3545", "badge_bg": "#C0392B", "badge_text": "RISK FLAGGED"},
    "oppt":   {"bg": "#E2D9F3", "border": "#6F42C1", "badge_bg": "#6F42C1", "badge_text": "OPPORTUNITY"},
}

def finding(observation: str, implication: str, priority: str = "medium",
            metric: str = None, metric_label: str = None):
    """
    Build a single finding dict.
    observation  : what the data shows
    implication  : the commercial/procurement "so what"
    priority     : "high" | "medium" | "low" | "risk" | "oppt"
    metric       : optional headline number (e.g. "₹2,400 Cr")
    metric_label : label for the metric (e.g. "Estimated import cost if Gram area falls 20%")
    """
    return {
        "observation": observation,
        "implication": implication,
        "priority": priority,
        "metric": metric,
        "metric_label": metric_label,
    }

def so_what(module_name: str, findings: list, collapsed: bool = False):
    """
    Render a "Key Findings & So What" callout box with structured findings.
    findings : list of dicts from finding()
    collapsed : whether to render inside an expander
    """
    n_high = sum(1 for f in findings if f["priority"] in ("high", "risk"))
    header = (
        f"📌 Key Findings — {module_name}  "
        f"{'  🔴 ' + str(n_high) + ' high-priority item(s)' if n_high > 0 else ''}"
    )

    def _render():
        for idx, f in enumerate(findings):
            c = PRIORITY_COLORS.get(f["priority"], PRIORITY_COLORS["medium"])

            metric_html = ""
            if f.get("metric"):
                metric_html = (
                    f"<div style='margin-top:6px;'>"
                    f"<span style='font-size:1.4rem;font-weight:700;color:{c['border']}'>{f['metric']}</span>"
                    f"<span style='font-size:0.78rem;color:#555;margin-left:6px'>{f.get('metric_label','')}</span>"
                    f"</div>"
                )

            html = f"""
            <div style='
                background:{c["bg"]};
                border-left:5px solid {c["border"]};
                border-radius:6px;
                padding:12px 16px;
                margin-bottom:10px;
            '>
                <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>
                    <span style='
                        background:{c["badge_bg"]};
                        color:white;
                        font-size:0.68rem;
                        font-weight:700;
                        padding:2px 8px;
                        border-radius:3px;
                        letter-spacing:0.05em;
                    '>{c["badge_text"]}</span>
                    <span style='font-weight:600;font-size:0.92rem;color:#1a1a1a'>{f["observation"]}</span>
                </div>
                <div style='font-size:0.85rem;color:#333;margin-left:2px'>
                    <b>→ So what:</b> {f["implication"]}
                </div>
                {metric_html}
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

    if collapsed:
        with st.expander(header, expanded=False):
            _render()
    else:
        st.markdown(
            f"<div style='background:#F4F6F8;border:1px solid #DDE2E8;border-radius:8px;"
            f"padding:14px 18px 6px 18px;margin-bottom:18px;'>"
            f"<div style='font-size:0.95rem;font-weight:700;color:#2C3E50;margin-bottom:10px'>"
            f"{header}</div></div>",
            unsafe_allow_html=True
        )
        _render()
