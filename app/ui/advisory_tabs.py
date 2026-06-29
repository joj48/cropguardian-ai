# advisory_tabs.py — CropGuardian AI Scientific KB & AI Advisor Renderer
import streamlit as st
from ui.prediction_card import format_disease_name

def render_bullet_list(items: list):
    """Renders a list of items using clean Streamlit markdown bullets."""
    if not items:
        st.caption("No recommendations available.")
        return
    for item in items:
        st.markdown(f"- {item}")

def render_advisory_section(knowledge_ctx: dict, advice_res: dict):
    """
    Renders scientific information and AI advice.
    Combines KB taxonomy, symptoms, and Gemini recommendations.
    """
    # ── 1. Scientific Identity Grid ──────────────────────────────────────────
    if knowledge_ctx:
        st.markdown("**Taxonomy & Classification**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write(f"- **Crop**: `{knowledge_ctx.get('crop', 'Unknown')}`")
        with c2:
            st.write(f"- **Common Name**: `{knowledge_ctx.get('common_name', 'Unknown')}`")
        with c3:
            st.write(f"- **Scientific**: *{knowledge_ctx.get('scientific_name', 'Unknown')}*")
        with c4:
            st.write(f"- **Pathogen Type**: `{knowledge_ctx.get('pathogen_type', 'Unknown')}`")
        st.divider()

    # ── 2. Immediate Actions Alert ───────────────────────────────────────────
    immediate = (advice_res or {}).get("immediate_actions") or (knowledge_ctx or {}).get("immediate_actions")
    if immediate:
        if isinstance(immediate, list):
            immediate = " ".join(immediate)
        st.error(f"⚡ **Immediate Actions Required:** {immediate}")

    # ── 3. Weather Alerts ────────────────────────────────────────────────────
    weather_warn = (advice_res or {}).get("weather_based_warnings") or (knowledge_ctx or {}).get("weather_based_warnings")
    if weather_warn and weather_warn not in ("None.", "N/A", "None"):
        st.warning(f"🌦️ **Weather Alert:** {weather_warn}")

    st.markdown("")

    # ── 4. Main Advisory Content (Columns) ────────────────────────────────────
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🧪 Treatment Recommendations")
        # Extract treatment from AI advice or KB
        treatment = (advice_res or {}).get("treatment") or (knowledge_ctx or {}).get("treatment")
        if isinstance(treatment, dict):
            for k, v in treatment.items():
                st.markdown(f"**{k.replace('_', ' ').title()}**")
                if isinstance(v, list):
                    render_bullet_list(v)
                else:
                    st.write(v)
        elif isinstance(treatment, list):
            render_bullet_list(treatment)
        elif treatment:
            st.write(treatment)
        else:
            st.caption("No treatment recommendations logged.")
            
    with col2:
        st.markdown("### 🛡️ Prevention & Management")
        prevention = (advice_res or {}).get("prevention") or (knowledge_ctx or {}).get("prevention")
        if isinstance(prevention, dict):
            for k, v in prevention.items():
                st.markdown(f"**{k.replace('_', ' ').title()}**")
                if isinstance(v, list):
                    render_bullet_list(v)
                else:
                    st.write(v)
        elif isinstance(prevention, list):
            render_bullet_list(prevention)
        elif prevention:
            st.write(prevention)
        else:
            st.caption("No preventive recommendations logged.")

    st.divider()

    # ── 5. Symptoms & Progression ──────────────────────────────────────────
    if knowledge_ctx:
        col_sym1, col_sym2 = st.columns(2)
        with col_sym1:
            symptoms = knowledge_ctx.get("symptoms")
            if symptoms:
                st.markdown("### 🩺 Identified Symptoms")
                if isinstance(symptoms, list):
                    render_bullet_list(symptoms)
                elif isinstance(symptoms, dict):
                    for k, v in symptoms.items():
                        st.markdown(f"**{k.replace('_', ' ').title()}**")
                        if isinstance(v, list):
                            render_bullet_list(v)
                        else:
                            st.write(v)
                else:
                    st.write(symptoms)
        with col_sym2:
            progression = knowledge_ctx.get("disease_progression") or knowledge_ctx.get("infection_cycle")
            if progression:
                st.markdown("### 🔄 Cycle & Progression")
                if isinstance(progression, list):
                    render_bullet_list(progression)
                else:
                    st.write(progression)
        st.divider()

    # ── 6. Additional Nutrition & Expert consultation ────────────────────────
    fertilizer = (advice_res or {}).get("fertilizer_recommendations") or (knowledge_ctx or {}).get("fertilizer_recommendations")
    consultation = (advice_res or {}).get("expert_consultation") or (knowledge_ctx or {}).get("expert_consultation")
    
    if fertilizer or consultation:
        col_extra1, col_extra2 = st.columns(2)
        with col_extra1:
            if fertilizer:
                st.markdown("### 🌱 Nutrition & Fertilizer Guidance")
                if isinstance(fertilizer, list):
                    render_bullet_list(fertilizer)
                else:
                    st.write(fertilizer)
        with col_extra2:
            if consultation:
                st.markdown("### 👨‍🌾 Expert Consultation Advice")
                st.info(consultation)
        st.divider()

    # ── 7. Frequently Asked Questions (FAQ) ──────────────────────────────────
    faq = (knowledge_ctx or {}).get("faq")
    if faq and isinstance(faq, list):
        st.markdown("### ❓ FAQ")
        for item in faq:
            if isinstance(item, dict) and "question" in item and "answer" in item:
                with st.expander(item["question"]):
                    st.write(item["answer"])

    # ── 8. References ────────────────────────────────────────────────────────
    refs = (knowledge_ctx or {}).get("references")
    if refs:
        with st.expander("🎓 Scientific Resources & References"):
            if isinstance(refs, list):
                render_bullet_list(refs)
            else:
                st.write(refs)

    # ── 9. Source metadata ───────────────────────────────────────────────────
    source = (advice_res or {}).get("source") or (knowledge_ctx or {}).get("source")
    if source:
        st.caption(f"Advisory Source: `{source}`")
