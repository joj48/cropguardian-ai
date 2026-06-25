import streamlit as st

st.set_page_config(
    page_title="CropGuardian AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌿 CropGuardian AI")
st.markdown("""
Welcome to the **CropGuardian AI** end-to-end MVP.

Use the sidebar to navigate between:
* **Disease Detection:** Upload an image for real-time predictions and immediate feedback.
* **Feedback:** Submit manual misclassification reports to improve the model.
* **History:** View past predictions securely logged in the system.
* **Model Insights:** View comprehensive analytics from the Evaluation Pipeline.

👈 Select a page from the sidebar to get started!
""")
