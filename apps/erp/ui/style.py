# ui/style.py
import streamlit as st

def inject_style():
    st.markdown(
        """
        <style>
            body { background-color: #F5F7F2; color: #2F3E2C; }
            .sidebar .sidebar-content { background-color: #E8F0E1 !important; }
            .stButton>button { background-color: #4B7F4A; color: white; border-radius: 6px; border: none; }
            .stButton>button:hover { background-color: #3A6A38; }
            .green-card { padding: 12px; border-radius: 8px; background-color: #EBF4E5; border-left: 6px solid #4B7F4A; }
        </style>
        """,
        unsafe_allow_html=True
    )

def green_title(text: str):
    st.markdown(f"<div class='green-card'><h2>{text}</h2></div>", unsafe_allow_html=True)

def green_sub(text: str):
    st.markdown(f"#### {text}")

def green_card(text: str):
    st.markdown(f"<div class='green-card'>{text}</div>", unsafe_allow_html=True)
