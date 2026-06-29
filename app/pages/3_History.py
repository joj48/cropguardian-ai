import os
import sys
import datetime
import pandas as pd
import streamlit as st

# Ensure path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui import init_page, render_header, render_footer, format_disease_name

# Initialize Page (Page Config, Navigation Sidebar, CSS)
init_page(title="Prediction History", icon="📜")

# ─── Sidebar Page-Specific Advice ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("**📜 Prediction Logs**")
    st.caption(
        "All agricultural diagnostic runs are automatically persisted here on execution."
    )

# Page Header
render_header("📜 Prediction History", "Browse and export records of past diagnoses executed by the multi-agent system.")

HISTORY_CSV = "data/history/prediction_log.csv"

if not os.path.exists(HISTORY_CSV):
    st.info("No prediction history log found. Run a crop diagnosis on the Disease Detection page first.")
    st.stop()

# ─── Load Data ───────────────────────────────────────────────────────────────
try:
    df = pd.read_csv(HISTORY_CSV)
except Exception as e:
    st.error(f"Could not load prediction log: {e}")
    st.stop()

if df.empty:
    st.info("The prediction history log is empty. No diagnoses have been logged yet.")
    st.stop()

# Sort by timestamp descending
if "timestamp" in df.columns:
    df = df.sort_values(by="timestamp", ascending=False).reset_index(drop=True)

# ─── Prediction Metrics Summary ───────────────────────────────────────────────
total = len(df)
diseases_detected = df["predicted_class"].nunique() if "predicted_class" in df.columns else 0
avg_conf = round(df["confidence"].astype(float).mean(), 1) if "confidence" in df.columns else 0.0

st.markdown("<div class='cg-section-label'>Historical Summary Metrics</div>", unsafe_allow_html=True)
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total Predictions", f"{total:,}")
with m2:
    st.metric("Diseases Detected", f"{diseases_detected}")
with m3:
    st.metric("Average Confidence", f"{avg_conf}%")

st.divider()

# ─── Filters & Export Actions ────────────────────────────────────────────────
st.markdown("<div class='cg-section-label'>Diagnosis Records</div>", unsafe_allow_html=True)

# Export download payloads
df_export = df.copy()
if "predicted_class" in df_export.columns:
    df_export["predicted_class_raw"] = df_export["predicted_class"]
    df_export["predicted_class"] = df_export["predicted_class"].apply(format_disease_name)

# Expose filter
conf_levels = ["All"] + sorted(df["confidence_level"].dropna().unique().tolist()) if "confidence_level" in df.columns else ["All"]

filter_col, export_col = st.columns([2, 3], gap="medium")
with filter_col:
    selected_level = st.selectbox(
        "Filter by Confidence Level",
        conf_levels,
        label_visibility="visible",
    )

filtered_df = df_export.copy()
if selected_level != "All" and "confidence_level" in df.columns:
    filtered_df = filtered_df[filtered_df["confidence_level"] == selected_level]

with export_col:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) # spacing
    btn1, btn2, btn3 = st.columns(3)
    
    with btn1:
        st.download_button(
            "⬇️ Export CSV",
            data=filtered_df.to_csv(index=False),
            file_name="cropguardian_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with btn2:
        st.download_button(
            "⬇️ Export JSON",
            data=filtered_df.to_json(orient="records", indent=2),
            file_name="cropguardian_history.json",
            mime="application/json",
            use_container_width=True,
        )
    with btn3:
        # Generate diagnostic report markdown
        report_markdown = f"""# CropGuardian AI History Export Report
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---
- Total Diagnostic Log Runs: {total}
- Unique Pathogens Identified: {diseases_detected}
- Average Inference Confidence: {avg_conf}%
- Total Filtered Records: {len(filtered_df)}
"""
        st.download_button(
            "⬇️ Export Report",
            data=report_markdown,
            file_name="cropguardian_summary_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

# Configure columns
column_config = {}
if "confidence" in filtered_df.columns:
    column_config["confidence"] = st.column_config.ProgressColumn(
        "Confidence",
        min_value=0,
        max_value=100,
        format="%.1f%%",
    )
if "timestamp" in filtered_df.columns:
    column_config["timestamp"] = st.column_config.TextColumn("Timestamp", width="medium")
if "predicted_class" in filtered_df.columns:
    column_config["predicted_class"] = st.column_config.TextColumn("Detected Disease", width="large")
if "image_name" in filtered_df.columns:
    column_config["image_name"] = st.column_config.TextColumn("Image Source File", width="medium")

# Render table
st.data_editor(
    filtered_df.drop(columns=["predicted_class_raw"], errors="ignore"),
    disabled=True,
    use_container_width=True,
    hide_index=True,
    column_config=column_config,
)
st.caption(f"Displaying {len(filtered_df)} of {total} total records.")

render_footer()
