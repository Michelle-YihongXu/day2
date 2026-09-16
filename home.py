import streamlit as st
import os
from dotenv import load_dotenv

# Load local .env file
load_dotenv()


# ---------------------------------
# Get password
# Works locally AND on Streamlit Cloud
# ---------------------------------

def get_app_password():
    # First try Streamlit Cloud Secrets
    try:
        return st.secrets["PASSWORD"]
    except Exception:
        # If running locally, use .env
        return os.getenv("PASSWORD")


# ---------------------------------
# Password protection
# ---------------------------------

def check_password():

    correct_password = get_app_password()

    # Already authenticated in this session
    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 Private App")

    password = st.text_input(
        "Enter password to continue",
        type="password"
    )

    if password:

        if password == correct_password:
            st.session_state["password_correct"] = True
            st.rerun()

        else:
            st.error("Incorrect password")

    return False


# STOP everything if password is incorrect
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