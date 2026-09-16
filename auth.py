import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()


def get_app_password():
    # Streamlit Cloud
    try:
        return st.secrets["PASSWORD"]
    except Exception:
        # Local Codespaces / .env
        return os.getenv("PASSWORD")


def require_password():

    correct_password = get_app_password()

    # Already logged in during this session
    if st.session_state.get("password_correct", False):
        return

    st.title("🔒 Private App")

    password = st.text_input(
        "Enter password to continue",
        type="password"
    )

    if password == correct_password and password:
        st.session_state["password_correct"] = True
        st.rerun()

    if password:
        st.error("❌ Incorrect password")

    st.stop()