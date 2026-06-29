# prediction_card.py — CropGuardian AI Disease Identification Renderer
import pandas as pd
import streamlit as st

def format_disease_name(disease_class: str) -> str:
    """Formats raw crop-disease identifier names into a human-readable display string."""
    if not disease_class:
        return "Unknown"
    if "___" in disease_class:
        plant_raw, disease_raw = disease_class.split("___", 1)
        plant = plant_raw.replace(",", "").replace("_", " ").strip().title()
        disease = disease_raw.replace("_", " ").strip().title()
        return f"{plant} — {disease}"
    return disease_class.replace("_", " ").title()

def is_healthy(disease_class: str) -> bool:
    """Returns True if the predicted class is healthy."""
    return "healthy" in (disease_class or "").lower()

def render_prediction_card(prediction: dict, severity_res: dict, risk_data: dict):
    """Renders the prediction results, metrics, and native confidence charts."""
    disease_class = prediction.get("disease", "Unknown")
    confidence = prediction.get("confidence", 0)
    confidence_level = prediction.get("confidence_level", "Unknown")
    severity = severity_res.get("severity", "Unknown")
    sev_score = severity_res.get("severity_score", 0)
    spread_prob = risk_data.get("spread_probability", 0) if (risk_data and "error" not in risk_data) else 0
    healthy = is_healthy(disease_class)

    with st.container(border=True):
        st.markdown(
            f'<div class="cg-disease-hero {"cg-disease-healthy" if healthy else ""}">'
            f'{format_disease_name(disease_class)}</div>',
            unsafe_allow_html=True,
        )

        # Native badges using Streamlit markdown styling
        status_color = ":green" if healthy else ":red"
        conf_color = ":green" if confidence >= 85 else ":orange"
        sev_color = ":green" if severity == "Low" else (":orange" if severity == "Medium" else ":red")
        
        st.markdown(
            f"Confidence: {conf_color}[{confidence_level}] &nbsp;|&nbsp; "
            f"Severity: {sev_color}[{severity}] &nbsp;|&nbsp; "
            f"Risk Level: {status_color}[{risk_data.get('overall_risk', 'N/A')}]"
        )

        if prediction.get("warning"):
            st.warning(prediction["warning"])

        st.divider()

        # Detailed metrics columns
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Confidence", f"{confidence}%")
            st.progress(confidence / 100)
        with c2:
            st.metric("Severity Score", f"{sev_score} / 3")
            st.progress(sev_score / 3)
        with c3:
            st.metric("Spread Risk", f"{spread_prob}%")
            st.progress(spread_prob / 100)

def render_top_predictions_chart(prediction: dict):
    """Renders the top prediction probabilities using a native Streamlit chart."""
    top_predictions = prediction.get("top_predictions", [])
    if not top_predictions:
        st.caption("No additional predictions available.")
        return

    st.markdown("**Top Predictions Probability**")
    
    chart_data = {
        "Disease": [format_disease_name(p["class"]) for p in top_predictions],
        "Confidence (%)": [p["confidence"] for p in top_predictions]
    }
    df_chart = pd.DataFrame(chart_data).set_index("Disease")
    
    st.bar_chart(df_chart, y="Confidence (%)", use_container_width=True)
