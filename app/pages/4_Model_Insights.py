import os
import sys
import json
import glob
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.feedback_agent.feedback_agent import FeedbackAgent

st.set_page_config(page_title="Model Insights", page_icon="📊", layout="wide")

st.title("📊 Model Insights")
st.markdown("View comprehensive analytics and feedback statistics for the model.")

# --- Evaluation Reports ---
st.header("Evaluation Pipeline Reports")
reports_dir = "reports"

if not os.path.exists(reports_dir):
    # Fallback to reports_dummy if present for testing
    if os.path.exists("reports_dummy"):
        reports_dir = "reports_dummy"

if os.path.exists(reports_dir):
    # Find available metrics files
    metrics_files = glob.glob(os.path.join(reports_dir, "*_metrics.json"))
    
    if metrics_files:
        # Extract prefixes
        prefixes = [os.path.basename(f).replace("_metrics.json", "") for f in metrics_files]
        selected_prefix = st.selectbox("Select Evaluation Dataset", prefixes)
        
        col1, col2 = st.columns(2)
        
        # Load Metrics
        metrics_path = os.path.join(reports_dir, f"{selected_prefix}_metrics.json")
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            with col1:
                st.metric("Overall Accuracy", f"{metrics.get('accuracy', 0)*100:.2f}%")
            with col2:
                st.metric("Weighted F1 Score", f"{metrics.get('f1_score', 0):.4f}")
        except Exception as e:
            st.error(f"Error loading metrics: {e}")
            
        st.divider()
        
        # Confusion Matrix
        cm_path = os.path.join(reports_dir, f"{selected_prefix}_confusion_matrix.png")
        if os.path.exists(cm_path):
            st.subheader("Confusion Matrix")
            st.image(cm_path, width=800)
            
        st.divider()
        
        # Model Health Report
        health_path = os.path.join(reports_dir, f"{selected_prefix}_model_health_report.md")
        if os.path.exists(health_path):
            st.subheader("Model Health Report")
            with open(health_path, 'r') as f:
                st.markdown(f.read())
    else:
        st.info("No evaluation metrics found in reports directory.")
else:
    st.info("Reports directory not found. Please run the Evaluation Pipeline first.")

st.divider()

# --- Feedback Statistics ---
st.header("Feedback Statistics")
st.markdown("Real-time statistics gathered from user corrections.")

@st.cache_resource
def get_feedback_agent():
    return FeedbackAgent()

agent = get_feedback_agent()
stats = agent.get_feedback_stats()

f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    st.metric("Total Feedback Logs", stats["total_feedback"])
with f_col2:
    confused_class = stats["most_confused_class"] if stats["most_confused_class"] else "N/A"
    st.metric("Most Confused Class", confused_class)
with f_col3:
    st.metric("Avg Wrong Confidence", f"{stats['average_wrong_confidence']}%")

if stats["total_feedback"] > 0:
    st.success("Feedback system is actively collecting data for retraining.")
else:
    st.info("No feedback has been logged yet.")
