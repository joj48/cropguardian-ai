import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Prediction History", page_icon="📜", layout="wide")

st.title("📜 Prediction History")
st.markdown("A complete log of all predictions made through the frontend interface.")

history_csv = "data/history/prediction_log.csv"

if os.path.exists(history_csv):
    try:
        df = pd.read_csv(history_csv)
        # Sort by timestamp descending
        if "timestamp" in df.columns:
            df = df.sort_values(by="timestamp", ascending=False)
            
        st.dataframe(df, use_container_width=True)
        
        st.download_button(
            label="Download History CSV",
            data=df.to_csv(index=False),
            file_name="prediction_history.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Could not load history: {e}")
else:
    st.info("No prediction history found. Run a prediction on the Disease Detection page first.")
