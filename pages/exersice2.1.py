import streamlit as st
import pandas as pd
from io import StringIO
from pypdf import PdfReader


st.title("Exercise 2.1")


# 1. Allows the user to upload a document.
uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        st.write(text)
    else:
        bytes_data = uploaded_file.getvalue()
        string_data = bytes_data.decode("utf-8")
        st.write(string_data)