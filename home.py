import streamlit as st
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()


# ---------------------------------
# Password protection
# ---------------------------------

def check_password():
    """Require a password before accessing the app."""

    correct_password = os.getenv("PASSWORD")

    # If already logged in, allow access
    if st.session_state.get("password_correct", False):
        return True

    # Password input
    password = st.text_input(
        "🔒 Enter password to access this app",
        type="password"
    )

    # Check password
    if password:
        if password == correct_password:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Incorrect password")

    return False


# Stop the app here unless password is correct
if not check_password():
    st.stop()


# ---------------------------------
# Main application
# ---------------------------------

st.title("Day 2")

st.header("How to Setup Streamlit Application")

st.write(
    "Step 1. Create home.py file, using 'touch home.py' in the terminal."
)

st.write(
    "Step 2. Run streamlit webserver, using 'streamlit run home.py' in the terminal."
)