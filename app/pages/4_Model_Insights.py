import os
import sys
import json
import glob
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.feedback_agent.feedback_agent import FeedbackAgent
from ui import init_page, render_header, render_footer

# Initialize Page (Sets config, sidebars, styles)
init_page(title="Model Insights", icon="📊")

@st.cache_resource
def get_feedback_agent():
    return FeedbackAgent()

feedback_agent = get_feedback_agent()

# ─── Sidebar Page-Specific Advice ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("**📊 Model Telemetry**")
    st.caption(
        "Accuracy reports represent standard test splits. "
        "Dynamic statistics represent user corrections."
    )

# Page Header
render_header("📊 Model Insights", "View classification accuracy records, confusion matrices, and live user feedback statistics.")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION A: EVALUATION PIPELINE REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='cg-section-label'>Evaluation Pipeline Reports</div>", unsafe_allow_html=True)

reports_dir = "reports"
if not os.path.exists(reports_dir) and os.path.exists("reports_dummy"):
    reports_dir = "reports_dummy"

if not os.path.exists(reports_dir):
    with st.container(border=True):
        st.markdown("### No evaluation records found")
        st.caption(
            "Evaluation metrics will be generated on executing `src/evaluation/metrics.py`. "
            "Reports are placed under `reports/` and display dataset precision and classification details."
        )
    st.divider()
else:
    metrics_files = glob.glob(os.path.join(reports_dir, "*_metrics.json"))
    if not metrics_files:
        st.info("No evaluation metric reports found in the directory.")
    else:
        prefixes = [os.path.basename(f).replace("_metrics.json", "") for f in metrics_files]
        selected_prefix = st.selectbox(
            "Select Evaluation Dataset",
            prefixes,
            label_visibility="visible",
        )

        metrics_path = os.path.join(reports_dir, f"{selected_prefix}_metrics.json")
        try:
            with open(metrics_path, "r") as f:
                metrics = json.load(f)

            # Performance metric columns
            st.markdown("<div class='cg-section-label'>Performance Metrics</div>", unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Overall Accuracy", f"{metrics.get('accuracy', 0) * 100:.2f}%")
            m2.metric("Weighted F1 Score", f"{metrics.get('f1_score', 0):.4f}")
            m3.metric("Weighted Precision", f"{metrics.get('precision', 0):.4f}")
            m4.metric("Weighted Recall", f"{metrics.get('recall', 0):.4f}")
        except Exception as e:
            st.error(f"Error loading metrics file: {e}")

        st.divider()

        # Confusion Matrix Image
        cm_path = os.path.join(reports_dir, f"{selected_prefix}_confusion_matrix.png")
        if os.path.exists(cm_path):
            st.markdown("<div class='cg-section-label'>Confusion Matrix</div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.image(cm_path, use_container_width=True)
            st.divider()

        # Model Health Report Text File
        health_path = os.path.join(reports_dir, f"{selected_prefix}_model_health_report.md")
        if os.path.exists(health_path):
            st.markdown("<div class='cg-section-label'>Model Health Report</div>", unsafe_allow_html=True)
            with st.container(border=True):
                try:
                    with open(health_path, "r") as f:
                        st.markdown(f.read())
                except Exception as e:
                    st.error(f"Error loading health report text: {e}")
            st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION B: LIVE FEEDBACK STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='cg-section-label'>Feedback Intelligence</div>", unsafe_allow_html=True)

stats = feedback_agent.get_feedback_stats()
total_feedback = stats.get("total_feedback", 0)
confused_class = stats.get("most_confused_class") or "N/A"
avg_wrong_conf = stats.get("average_wrong_confidence", 0)

f1, f2, f3 = st.columns(3)
with f1:
    with st.container(border=True):
        st.metric("Total Corrections Logged", total_feedback)
with f2:
    with st.container(border=True):
        st.metric("Most Confused Class", confused_class if len(str(confused_class)) < 30 else str(confused_class)[:27] + "…")
        if confused_class != "N/A":
            st.caption("Class corrected most frequently by farmers.")
with f3:
    with st.container(border=True):
        st.metric("Avg Confidence at Misprediction", f"{avg_wrong_conf}%")
        if avg_wrong_conf > 0:
            st.progress(avg_wrong_conf / 100)

if total_feedback > 0:
    st.success(
        f"Feedback system is active. {total_feedback} correction(s) have been saved to local "
        "logs and are available for model retraining."
    )
else:
    st.info("No user corrections have been submitted. If a prediction is inaccurate, report it via the Disease Detection page.")

render_footer()
