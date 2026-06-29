# styles.py — CropGuardian AI Shared Minimal Styles
import streamlit as st

def inject_css():
    """Injects CropGuardian AI global design system CSS."""
    st.markdown("""
    <style>
    /* Font override for text-content elements */
    .stApp,
    .stApp p,
    .stApp li,
    .stApp label,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stCaptionContainer"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter",
                     "Helvetica Neue", Arial, sans-serif;
    }

    /* Layout & Spacing */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.0rem !important;
        max-width: 1280px;
    }

    /* Section Labels */
    .cg-section-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--primary-color, #2E8B57);
        margin-bottom: 8px;
        margin-top: 4px;
    }

    /* Disease Hero Card */
    .cg-disease-hero {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.25;
        margin-bottom: 6px;
    }
    .cg-disease-healthy {
        color: var(--primary-color, #2E8B57);
    }

    /* Advisory List Items */
    .cg-adv-list { margin: 0; padding: 0; }
    .cg-adv-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 6px 0;
        border-bottom: 1px solid rgba(128, 128, 128, 0.1);
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .cg-adv-item:last-child { border-bottom: none; }
    .cg-adv-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--primary-color, #2E8B57);
        margin-top: 7px;
        flex-shrink: 0;
    }

    /* Risk Reason Bar */
    .cg-reason {
        font-size: 0.85rem;
        padding: 4px 0 4px 12px;
        border-left: 2px solid rgba(128, 128, 128, 0.3);
        margin: 3px 0;
        line-height: 1.5;
    }

    /* How-It-Works Step Cards (home page) */
    .cg-step-icon {
        font-size: 1.8rem;
        margin-bottom: 8px;
    }
    .cg-step-title {
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .cg-step-desc {
        font-size: 0.82rem;
        color: var(--text-color, #333333);
        opacity: 0.8;
        line-height: 1.45;
    }

    /* Stat number on home */
    .cg-stat-num {
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--primary-color, #2E8B57);
        letter-spacing: -0.03em;
        line-height: 1;
    }
    .cg-stat-lbl {
        font-size: 0.82rem;
        margin-top: 4px;
        opacity: 0.7;
    }
    </style>
    """, unsafe_allow_html=True)
