"""
ui_components.py — CropGuardian AI Shared Design System

Provides:
  - inject_css(): Global CSS injection (fonts, cards, badges, layout tweaks)
  - render_badge(level): Color-coded HTML badge for risk/severity/confidence levels
  - render_section_label(text): Uppercase section label with accent color
  - format_disease_name(disease_class): "Tomato___Late_blight" → "Tomato — Late Blight"
  - render_advisory_list(items): Styled bullet list for advisory items
  - render_callout(text, kind): Styled callout box (action/warning/success)
  - render_prediction_summary(response): 6-column status dashboard panel
  - render_ai_advisory(advice): Renders Gemini personalized advisory section
  - KnowledgeBasePresentationEngine: Schema-driven KB renderer

Only used by app/ files. No backend imports.
"""

import streamlit as st

# ─── Color map for risk/severity/confidence levels ──────────────────────────

LEVEL_COLORS = {
    "High":     {"bg": "rgba(239,68,68,0.14)",   "text": "#f87171", "border": "rgba(239,68,68,0.35)"},
    "Very High":{"bg": "rgba(239,68,68,0.20)",   "text": "#ef4444", "border": "rgba(239,68,68,0.50)"},
    "Medium":   {"bg": "rgba(245,158,11,0.14)",  "text": "#fbbf24", "border": "rgba(245,158,11,0.35)"},
    "Low":      {"bg": "rgba(34,197,94,0.14)",   "text": "#4ade80", "border": "rgba(34,197,94,0.35)"},
    "None":     {"bg": "rgba(107,114,128,0.14)", "text": "#9ca3af", "border": "rgba(107,114,128,0.30)"},
    "N/A":      {"bg": "rgba(107,114,128,0.14)", "text": "#9ca3af", "border": "rgba(107,114,128,0.30)"},
    "Unknown":  {"bg": "rgba(107,114,128,0.14)", "text": "#9ca3af", "border": "rgba(107,114,128,0.30)"},
    "Healthy":  {"bg": "rgba(34,197,94,0.14)",   "text": "#4ade80", "border": "rgba(34,197,94,0.35)"},
}


# ─── Global CSS ──────────────────────────────────────────────────────────────

def inject_css():
    """Injects the CropGuardian AI global design system CSS into the page."""
    st.markdown("""
    <style>
    /* ── Font override ───────────────────────────────────────────────────────
       IMPORTANT: Do NOT use [class*="st-"] or !important here.
       Streamlit 1.41+ uses Material Icons as a glyph font on elements
       with class names like "st-*". Overriding font-family on those classes
       (especially with !important) breaks icon rendering — glyphs fall back
       to their raw text names: "arrow_right", "keyboard_double_arrow_right",
       "upload", etc.
       
       We only override font on known text-content elements. ──────────────── */
    .stApp,
    .stApp p,
    .stApp li,
    .stApp label,
    .stApp input,
    .stApp textarea,
    .stApp select,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"],
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"],
    [data-testid="stNotification"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter",
                     "Helvetica Neue", Arial, sans-serif;
    }

    /* ── Layout & Spacing ─────────────────────────────────────────────────── */
    .block-container {
        padding-top: 1.6rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1280px;
    }

    /* ── Metric Component Overrides ──────────────────────────────────────── */
    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.70rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
        color: #9ba3b2 !important;
    }
    [data-testid="stMetricDeltaIcon"],
    [data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }

    /* ── Tabs ─────────────────────────────────────────────────────────────── */
    [data-testid="stTabs"] [role="tablist"] {
        gap: 4px;
    }
    [data-testid="stTabs"] [role="tab"] {
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 6px 14px !important;
        border-radius: 6px 6px 0 0 !important;
    }

    /* ── Progress Bar ─────────────────────────────────────────────────────── */
    [data-testid="stProgress"] > div > div {
        border-radius: 4px !important;
    }

    /* ── Button ──────────────────────────────────────────────────────────── */
    [data-testid="baseButton-primary"] {
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
    }

    /* ── File Uploader ───────────────────────────────────────────────────── */
    [data-testid="stFileUploader"] section {
        border-radius: 10px !important;
    }

    /* ── Section Label ───────────────────────────────────────────────────── */
    .cg-section-label {
        font-size: 0.67rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #4ade80;
        margin-bottom: 8px;
        margin-top: 4px;
    }

    /* ── Disease Hero ────────────────────────────────────────────────────── */
    .cg-disease-hero {
        font-size: 1.65rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: #f1f5f9;
        line-height: 1.2;
        margin-bottom: 4px;
    }
    .cg-disease-healthy {
        color: #4ade80;
    }

    /* ── Badge Row ───────────────────────────────────────────────────────── */
    .cg-badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
        margin-top: 10px;
    }
    .cg-badge-label {
        font-size: 0.72rem;
        color: #9ba3b2;
        font-weight: 500;
    }

    /* ── Advisory List Items ─────────────────────────────────────────────── */
    .cg-adv-list { margin: 0; padding: 0; }
    .cg-adv-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        font-size: 0.88rem;
        color: #d1d5db;
        line-height: 1.5;
    }
    .cg-adv-item:last-child { border-bottom: none; }
    .cg-adv-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #4ade80;
        margin-top: 7px;
        flex-shrink: 0;
    }

    /* ── Risk Reason Bar ─────────────────────────────────────────────────── */
    .cg-reason {
        font-size: 0.82rem;
        color: #9ca3af;
        padding: 5px 0 5px 12px;
        border-left: 2px solid #374151;
        margin: 3px 0;
        line-height: 1.5;
    }

    /* ── Callout Boxes ───────────────────────────────────────────────────── */
    .cg-action-box {
        background: rgba(239,68,68,0.08);
        border: 1px solid rgba(239,68,68,0.28);
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.87rem;
        color: #fca5a5;
        line-height: 1.5;
        margin-bottom: 8px;
    }
    .cg-warning-box {
        background: rgba(245,158,11,0.08);
        border: 1px solid rgba(245,158,11,0.28);
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.87rem;
        color: #fcd34d;
        line-height: 1.5;
        margin-bottom: 8px;
    }
    .cg-success-box {
        background: rgba(34,197,94,0.08);
        border: 1px solid rgba(34,197,94,0.28);
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.87rem;
        color: #86efac;
        line-height: 1.5;
    }

    /* ── How-It-Works Step Cards (home page) ─────────────────────────────── */
    .cg-step-icon {
        font-size: 1.8rem;
        margin-bottom: 8px;
    }
    .cg-step-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 4px;
    }
    .cg-step-desc {
        font-size: 0.80rem;
        color: #9ba3b2;
        line-height: 1.5;
    }

    /* ── Sidebar Branding ────────────────────────────────────────────────── */
    [data-testid="stSidebarContent"] {
        padding-top: 1rem;
    }

    /* ── Stat number on home ─────────────────────────────────────────────── */
    .cg-stat-num {
        font-size: 2.2rem;
        font-weight: 800;
        color: #4ade80;
        letter-spacing: -0.03em;
        line-height: 1;
    }
    .cg-stat-lbl {
        font-size: 0.80rem;
        color: #9ba3b2;
        margin-top: 4px;
    }

    /* ── Prediction Summary Grid ──────────────────────────────────────────── */
    .cg-summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 10px;
        margin: 10px 0 4px 0;
    }
    .cg-summary-cell {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 10px 12px;
        text-align: center;
    }
    .cg-summary-cell-label {
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 5px;
    }
    .cg-summary-cell-value {
        font-size: 0.82rem;
        font-weight: 600;
        color: #e2e8f0;
        line-height: 1.3;
    }
    .cg-summary-ok   { color: #4ade80; }
    .cg-summary-warn { color: #fbbf24; }
    .cg-summary-err  { color: #f87171; }

    /* ── Identity Card (taxonomy fields) ─────────────────────────────────── */
    .cg-identity-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 8px;
        margin-bottom: 14px;
    }
    .cg-identity-cell {
        background: rgba(74,222,128,0.05);
        border: 1px solid rgba(74,222,128,0.15);
        border-radius: 8px;
        padding: 8px 12px;
    }
    .cg-identity-label {
        font-size: 0.60rem;
        font-weight: 700;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        color: #4ade80;
        margin-bottom: 3px;
    }
    .cg-identity-value {
        font-size: 0.82rem;
        font-weight: 500;
        color: #e2e8f0;
        font-style: italic;
    }

    /* ── AI Advisory Section ─────────────────────────────────────────────── */
    .cg-ai-source {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.70rem;
        color: #6b7280;
        margin-top: 10px;
        padding: 3px 10px;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
    }

    </style>
    """, unsafe_allow_html=True)


# ─── Component Helpers ────────────────────────────────────────────────────────

def render_badge(level: str) -> str:
    """Returns an inline HTML badge string for a risk/severity/confidence level."""
    c = LEVEL_COLORS.get(level, LEVEL_COLORS["Unknown"])
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:20px;'
        f'background:{c["bg"]};color:{c["text"]};border:1px solid {c["border"]};'
        f'font-size:0.75rem;font-weight:600;letter-spacing:0.03em;">{level}</span>'
    )


def render_section_label(text: str):
    """Renders a small uppercase section label with the brand green accent."""
    st.markdown(f'<div class="cg-section-label">{text}</div>', unsafe_allow_html=True)


def format_disease_name(disease_class: str) -> str:
    """
    Formats a raw PlantVillage class name into a readable label.
    Examples:
      'Tomato___Late_blight'       → 'Tomato — Late Blight'
      'Apple___Apple_scab'         → 'Apple — Apple Scab'
      'Tomato___healthy'           → 'Tomato — Healthy'
      'Pepper,_bell___Bacterial_spot' → 'Pepper Bell — Bacterial Spot'
    """
    if not disease_class:
        return "Unknown"
    if "___" in disease_class:
        plant_raw, disease_raw = disease_class.split("___", 1)
        plant = plant_raw.replace(",", "").replace("_", " ").strip().title()
        disease = disease_raw.replace("_", " ").strip().title()
        return f"{plant} — {disease}"
    return disease_class.replace("_", " ").title()


def is_healthy(disease_class: str) -> bool:
    """Returns True if the prediction is a healthy plant."""
    return "healthy" in (disease_class or "").lower()


def render_advisory_list(items: list):
    """
    Renders a list of advisory string items as styled HTML bullet points.
    Falls back to st.caption if the list is empty.
    """
    if not items:
        st.caption("No specific recommendations available.")
        return
    html = '<div class="cg-adv-list">'
    for item in items:
        html += f'<div class="cg-adv-item"><div class="cg-adv-dot"></div><div>{item}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_callout(text: str, kind: str = "warning"):
    """
    Renders a styled callout box.
    kind: 'action' (red), 'warning' (amber), 'success' (green)
    """
    icons = {"action": "⚡", "warning": "🌦", "success": "✅"}
    css_class = {"action": "cg-action-box", "warning": "cg-warning-box", "success": "cg-success-box"}
    icon = icons.get(kind, "ℹ️")
    cls = css_class.get(kind, "cg-warning-box")
    st.markdown(f'<div class="{cls}">{icon} {text}</div>', unsafe_allow_html=True)


def render_prediction_summary(response: dict):
    """
    Renders a compact 6-column pipeline status dashboard panel.
    Shows: Disease | Confidence | Knowledge | AI Advice | Weather | Workflow
    Consumed immediately after the Diagnosis Hero card.
    Supports both the new grouped schema and old flat schema.
    """
    # Safely extract from both new grouped and old flat schemas
    prediction   = response.get("prediction") or {}
    knowledge    = response.get("knowledge") or {}
    ai_section   = response.get("ai") or {}
    diagnostics  = response.get("diagnostics") or response  # flat fallback
    env_section  = response.get("environment") or {}

    # Resolve field values
    disease_name = format_disease_name(prediction.get("disease", "Unknown"))
    confidence   = prediction.get("confidence", 0)

    # Knowledge status
    kb_context   = knowledge.get("context")
    kb_status    = ("✅ Matched",  "cg-summary-ok") if kb_context else ("⚠️ Not Found", "cg-summary-warn")

    # AI status
    advice       = ai_section.get("advice") or response.get("advice")  # flat fallback
    ai_source    = (advice or {}).get("source", "")
    if advice and "gemini" in ai_source.lower():
        ai_status = ("✅ Generated", "cg-summary-ok")
    elif advice and ai_source:
        ai_status = ("📚 KB Fallback", "cg-summary-warn")
    elif advice:
        ai_status = ("✅ Available", "cg-summary-ok")
    else:
        ai_status = ("❌ Unavailable", "cg-summary-err")

    # Weather status
    weather       = env_section.get("weather") or response.get("weather")
    weather_ok    = weather and "error" not in weather and weather.get("status") not in ["unavailable", "timeout"]
    weather_status = ("✅ Retrieved", "cg-summary-ok") if weather_ok else ("⚠️ Unavailable", "cg-summary-warn")

    # Workflow
    engine = diagnostics.get("workflow_engine", "legacy_coordinator")
    workflow_label = "Google ADK" if "adk" in engine else "Legacy"
    workflow_cls   = "cg-summary-ok" if "adk" in engine else "cg-summary-warn"

    cells = [
        ("Disease",     disease_name,             "cg-summary-cell-value"),
        ("Confidence",  f"{confidence}%",          "cg-summary-ok" if confidence >= 85 else "cg-summary-warn"),
        ("Knowledge",   kb_status[0],              kb_status[1]),
        ("AI Advice",   ai_status[0],              ai_status[1]),
        ("Weather",     weather_status[0],         weather_status[1]),
        ("Workflow",    workflow_label,             workflow_cls),
    ]

    html = '<div class="cg-summary-grid">'
    for label, value, cls in cells:
        html += f'''
        <div class="cg-summary-cell">
            <div class="cg-summary-cell-label">{label}</div>
            <div class="cg-summary-cell-value {cls}">{value}</div>
        </div>'''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_ai_advisory(advice: dict):
    """
    Renders the Gemini-generated personalized advisory section.
    Displays action-oriented content only — does not duplicate KB scientific data.
    Supports both new schema (from response["ai"]["advice"]) and old flat schema.
    """
    if not advice:
        st.caption("No personalized AI advisory available for this prediction.")
        return

    # Immediate Actions — highest priority, rendered as red callout
    immediate = advice.get("immediate_actions", "")
    if immediate:
        render_callout(f"**Immediate Actions:** {immediate}", kind="action")

    # Weather Advisory
    weather_warning = advice.get("weather_based_warnings", "")
    if weather_warning and weather_warning not in ("None.", "N/A"):
        render_callout(f"**Weather Advisory:** {weather_warning}", kind="warning")

    # Recommendations in two columns
    treatment    = advice.get("treatment", [])
    prevention   = advice.get("prevention", [])
    fertilizer   = advice.get("fertilizer_recommendations", [])
    consultation = advice.get("expert_consultation", "")

    if treatment or prevention:
        left_col, right_col = st.columns(2, gap="medium")
        with left_col:
            if treatment:
                with st.container(border=True):
                    st.markdown("**🧪 Treatment Recommendations**")
                    render_advisory_list(treatment)
        with right_col:
            if prevention:
                with st.container(border=True):
                    st.markdown("**🛡️ Prevention**")
                    render_advisory_list(prevention)

    if fertilizer:
        with st.container(border=True):
            st.markdown("**🌱 Nutrition & Fertilizer**")
            render_advisory_list(fertilizer)

    if consultation:
        st.caption(f"👨‍⚕️ **Expert Consultation:** {consultation}")

    # Source badge
    source = advice.get("source", "")
    if source:
        st.markdown(
            f'<div class="cg-ai-source">🤖 Source: {source}</div>',
            unsafe_allow_html=True
        )


# ─── Knowledge Base Presentation Engine ───────────────────────────────────────

class KnowledgeBasePresentationEngine:
    """
    A schema-driven rendering engine that dynamically presents the CropGuardian
    Knowledge Base data in Streamlit.

    Consumes response["knowledge"]["context"] — the full DiseaseRecord as a dict.
    Three fixed tabs: Overview / Management / Additional Information.
    Unknown keys fall to Additional Information automatically.
    Internal KB fields (ai_context, prompt_templates, etc.) are silently ignored.
    """

    # Fields that are internal to the KB and must never be shown to farmers
    IGNORE_KEYS = {
        "metadata", "schema", "version",
        "model_mapping", "ai_context", "prompt_templates",
        "disease_id", "severity_levels", "severity_score",
        # Taxonomy fields rendered separately via render_identity_card()
        "disease_name", "common_name", "scientific_name",
        "crop", "disease_type", "pathogen_type",
        # Old advisory schema keys that may appear in legacy fallback
        "source", "expert_consultation",
        "disease_description",   # rendered as "overview" equivalent
    }

    # Taxonomy identity fields rendered as a card grid at the top of Overview
    IDENTITY_FIELDS = [
        ("common_name",     "Common Name"),
        ("scientific_name", "Scientific Name"),
        ("crop",            "Crop"),
        ("pathogen_type",   "Pathogen Type"),
        ("disease_type",    "Disease Type"),
    ]

    PRIORITY_MAP = {
        # Management tab — urgent first
        "immediate_actions":          1,
        "weather_based_warnings":     1,
        # Overview tab — identity and summary
        "overview":                   2,
        "symptoms":                   3,
        "causes":                     4,
        "infection_cycle":            5,
        "transmission":               6,
        "risk_factors":               7,
        "environmental_conditions":   8,
        "weather_influence":          9,
        "weather_thresholds":        10,
        # Management tab
        "treatment":                 11,
        "prevention":                12,
        "nutrient_management":       13,
        "fertilizer_recommendations":13,
        "disease_progression":       14,
        "recovery":                  15,
        "recovery_indicators":       16,
        "monitoring":                17,
        # Additional tab
        "economic_impact":           18,
        "educational_information":   19,
        "faq":                       20,
        "references":                21,
    }

    TAB_ROUTING = {
        "📋 Overview": [
            "overview", "disease_description",
            "symptoms", "causes", "infection_cycle", "transmission",
            "risk_factors", "environmental_conditions",
            "weather_influence", "weather_thresholds",
        ],
        "🛠️ Management": [
            "immediate_actions", "weather_based_warnings",
            "treatment", "prevention",
            "nutrient_management", "fertilizer_recommendations",
            "disease_progression", "recovery", "recovery_indicators",
            "monitoring",
        ],
        "📚 Additional Information": [
            "economic_impact", "educational_information",
            "faq", "references",
        ],
    }

    @classmethod
    def format_key(cls, key: str) -> str:
        return key.replace("_", " ").title()

    @classmethod
    def render(cls, knowledge_ctx: dict):
        """
        Main entry point. Accepts knowledge_ctx = response["knowledge"]["context"].
        Also accepts the old flat advisory dict as a graceful legacy fallback.
        """
        if not knowledge_ctx:
            st.caption("No Knowledge Base data available for this prediction.")
            return

        # Render taxonomy identity card at the top if KB fields are present
        cls._render_identity_card(knowledge_ctx)

        tabs_content = {
            "📋 Overview": {},
            "🛠️ Management": {},
            "📚 Additional Information": {},
        }

        for key, value in knowledge_ctx.items():
            if key in cls.IGNORE_KEYS or value in (None, "", [], {}):
                continue

            assigned_tab = "📚 Additional Information"
            for tab_name, keys in cls.TAB_ROUTING.items():
                if key in keys:
                    assigned_tab = tab_name
                    break

            tabs_content[assigned_tab][key] = value

        tab_names = list(tabs_content.keys())
        st_tabs = st.tabs(tab_names)

        for st_tab, tab_name in zip(st_tabs, tab_names):
            with st_tab:
                content = tabs_content[tab_name]
                if not content:
                    st.caption(f"No {tab_name.split()[1].lower()} information available.")
                    continue

                sorted_keys = sorted(
                    content.keys(),
                    key=lambda k: cls.PRIORITY_MAP.get(k, 999)
                )
                for key in sorted_keys:
                    cls._render_section(key, content[key])

    @classmethod
    def _render_identity_card(cls, knowledge_ctx: dict):
        """Renders taxonomy fields as a compact labelled identity grid."""
        cells = [
            (label, knowledge_ctx.get(field))
            for field, label in cls.IDENTITY_FIELDS
            if knowledge_ctx.get(field)
        ]
        if not cells:
            return

        html = '<div class="cg-identity-grid">'
        for label, value in cells:
            html += f'''
            <div class="cg-identity-cell">
                <div class="cg-identity-label">{label}</div>
                <div class="cg-identity-value">{value}</div>
            </div>'''
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    @classmethod
    def _render_section(cls, key: str, data):
        """Dispatches to specialized renderers or the generic node renderer."""
        if key == "immediate_actions":
            cls._render_immediate_actions(data)
            return
        elif key in ("weather_based_warnings", "weather_influence"):
            render_callout(f"**{cls.format_key(key)}:** {data}", kind="warning")
            return
        elif key == "references":
            cls._render_references(data)
            return
        elif key == "faq":
            cls._render_faq(data)
            return

        st.markdown(f"#### {cls.format_key(key)}")

        if isinstance(data, dict):
            keys = list(data.keys())
            if 1 < len(keys) <= 4 and all(isinstance(data[k], (list, str)) for k in keys):
                cols = st.columns(len(keys))
                for col, sub_key in zip(cols, keys):
                    with col:
                        with st.container(border=True):
                            st.markdown(f"**{cls.format_key(sub_key)}**")
                            cls._render_node(data[sub_key], depth=2)
            else:
                for sub_key, sub_val in data.items():
                    if not sub_val:
                        continue
                    with st.container(border=True):
                        st.markdown(f"**{cls.format_key(sub_key)}**")
                        cls._render_node(sub_val, depth=2)
        elif isinstance(data, list):
            cls._render_node(data, depth=1)
        elif isinstance(data, str):
            st.markdown(data)

    @classmethod
    def _render_node(cls, data, depth=1):
        """Recursively renders nested lists and dicts."""
        if isinstance(data, dict):
            for k, v in data.items():
                if not v:
                    continue
                st.markdown(f"**{cls.format_key(k)}**")
                if isinstance(v, list):
                    render_advisory_list(v)
                elif isinstance(v, dict):
                    st.json(v)
                else:
                    st.markdown(v)
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                for item in data:
                    title = item.get("title", item.get("name", "Item"))
                    with st.expander(title):
                        for k, v in item.items():
                            if k not in ("title", "name"):
                                st.markdown(f"**{cls.format_key(k)}**: {v}")
            else:
                render_advisory_list(data)
        elif isinstance(data, str):
            st.markdown(data)
        else:
            st.write(data)

    @classmethod
    def _render_immediate_actions(cls, data):
        if isinstance(data, list):
            action_text = " ".join(data)
            render_callout(f"**Immediate Actions Required:** {action_text}", kind="action")
        elif isinstance(data, str):
            render_callout(f"**Immediate Actions:** {data}", kind="action")
        elif isinstance(data, dict):
            today = data.get("today", [])
            if today:
                action_text = " ".join(today) if isinstance(today, list) else str(today)
                render_callout(f"**Immediate Action Required (Today):** {action_text}", kind="action")
            other_keys = [k for k in data.keys() if k != "today"]
            if other_keys:
                st.markdown("#### Additional Immediate Actions")
                cols = st.columns(min(len(other_keys), 3))
                for idx, key in enumerate(other_keys):
                    with cols[idx % len(cols)]:
                        with st.container(border=True):
                            st.markdown(f"**{cls.format_key(key)}**")
                            cls._render_node(data[key], depth=2)

    @classmethod
    def _render_references(cls, data):
        st.markdown("#### References")
        if isinstance(data, list):
            gov_refs, edu_refs, other_refs = [], [], []
            for ref in data:
                ref_lower = ref.lower()
                if ".gov" in ref_lower or "department" in ref_lower or "fda" in ref_lower:
                    gov_refs.append(ref)
                elif "university" in ref_lower or "extension" in ref_lower or "clinic" in ref_lower:
                    edu_refs.append(ref)
                else:
                    other_refs.append(ref)

            if edu_refs:
                with st.expander("🎓 Scientific & Extension Resources", expanded=True):
                    render_advisory_list(edu_refs)
            if gov_refs:
                with st.expander("🏛️ Government Sources"):
                    render_advisory_list(gov_refs)
            if other_refs:
                with st.expander("🌐 Additional References"):
                    render_advisory_list(other_refs)
        else:
            cls._render_node(data)

    @classmethod
    def _render_faq(cls, data):
        st.markdown("#### Frequently Asked Questions")
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "question" in item and "answer" in item:
                    with st.expander(item["question"]):
                        st.markdown(item["answer"])
                else:
                    st.write(item)
        else:
            cls._render_node(data)
