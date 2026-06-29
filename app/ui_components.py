"""
ui_components.py — CropGuardian AI Deprecated Compatibility Wrapper
All UI calls should be migrated to importing from the new `ui` package.
"""
import warnings
import streamlit as st
import ui

# Emit deprecation warning on import
warnings.warn(
    "ui_components.py is deprecated and will be removed in future versions. "
    "Please import from the modular `ui` package instead.",
    DeprecationWarning,
    stacklevel=2
)

# Preserve variables
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

def inject_css():
    import ui.styles
    ui.styles.inject_css()

def render_badge(level: str) -> str:
    # Keeps backward compatibility for inline HTML badges
    c = LEVEL_COLORS.get(level, LEVEL_COLORS["Unknown"])
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:20px;'
        f'background:{c["bg"]};color:{c["text"]};border:1px solid {c["border"]};'
        f'font-size:0.75rem;font-weight:600;letter-spacing:0.03em;">{level}</span>'
    )

def render_section_label(text: str):
    st.markdown(f'<div class="cg-section-label">{text}</div>', unsafe_allow_html=True)

def format_disease_name(disease_class: str) -> str:
    return ui.format_disease_name(disease_class)

def is_healthy(disease_class: str) -> bool:
    return ui.is_healthy(disease_class)

def render_advisory_list(items: list):
    ui.render_bullet_list(items)

def render_callout(text: str, kind: str = "warning"):
    if kind == "action":
        st.error(text)
    elif kind == "success":
        st.success(text)
    else:
        st.warning(text)

def render_prediction_summary(response: dict):
    # Backward-compatible 6-cell summary using st.columns
    prediction = response.get("prediction") or {}
    knowledge = response.get("knowledge") or {}
    ai_section = response.get("ai") or {}
    diagnostics = response.get("diagnostics") or response
    env_section = response.get("environment") or {}

    disease_name = format_disease_name(prediction.get("disease", "Unknown"))
    confidence = prediction.get("confidence", 0)
    kb_context = knowledge.get("context")
    kb_status = "✅ Matched" if kb_context else "⚠️ Not Found"

    advice = ai_section.get("advice") or response.get("advice")
    ai_source = (advice or {}).get("source", "")
    if advice and "gemini" in ai_source.lower():
        ai_status = "✅ Generated"
    elif advice:
        ai_status = "✅ Available"
    else:
        ai_status = "❌ Unavailable"

    weather = env_section.get("weather") or response.get("weather")
    weather_ok = weather and "error" not in weather and weather.get("status") not in ["unavailable", "timeout"]
    weather_status = "✅ Retrieved" if weather_ok else "⚠️ Unavailable"

    engine = diagnostics.get("workflow_engine", "legacy_coordinator")
    workflow_label = "Google ADK" if "adk" in engine else "Legacy"

    cols = st.columns(6)
    cols[0].metric("Disease", disease_name)
    cols[1].metric("Confidence", f"{confidence}%")
    cols[2].metric("Knowledge", kb_status)
    cols[3].metric("AI Advice", ai_status)
    cols[4].metric("Weather", weather_status)
    cols[5].metric("Workflow", workflow_label)

def render_ai_advisory(advice: dict):
    ui.render_advisory_section(None, advice)

class KnowledgeBasePresentationEngine:
    @classmethod
    def render(cls, knowledge_ctx: dict):
        ui.render_advisory_section(knowledge_ctx, None)
