import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np


# --------------------------------------------------
# Load environment variables and create OpenAI client
# --------------------------------------------------

load_dotenv()

client = OpenAI()


# --------------------------------------------------
# Page setup
# --------------------------------------------------

st.set_page_config(
    page_title="Comparing Chunks",
    page_icon="🔎",
    layout="wide"
)

st.title("Comparing Chunks")

st.write(
    "Paste two different chunks of text below. "
    "The application will create an embedding for each chunk "
    "and calculate their cosine similarity."
)


# --------------------------------------------------
# 1. Allow the user to paste two different texts
# --------------------------------------------------

text_1 = st.text_area(
    "Text 1",
    height=200,
    placeholder="Paste the first chunk of text here..."
)

text_2 = st.text_area(
    "Text 2",
    height=200,
    placeholder="Paste the second chunk of text here..."
)


# --------------------------------------------------
# 2. Function to create an embedding
# --------------------------------------------------

def create_embedding(text):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    embedding = response.data[0].embedding

    return embedding


# --------------------------------------------------
# 3. Function to calculate cosine similarity
# --------------------------------------------------

def cosine_similarity(vector_1, vector_2):

    vector_1 = np.array(vector_1)
    vector_2 = np.array(vector_2)

    dot_product = np.dot(vector_1, vector_2)

    magnitude_1 = np.linalg.norm(vector_1)
    magnitude_2 = np.linalg.norm(vector_2)

    similarity = dot_product / (magnitude_1 * magnitude_2)

    return similarity


# --------------------------------------------------
# 4. Compare the two chunks
# --------------------------------------------------

if st.button("Compare Texts"):

    if text_1 and text_2:

        with st.spinner("Creating embeddings..."):

            embedding_1 = create_embedding(text_1)
            embedding_2 = create_embedding(text_2)

            similarity = cosine_similarity(
                embedding_1,
                embedding_2
            )

        st.subheader("Cosine Similarity")

        st.write(similarity)

        st.metric(
            "Similarity Score",
            f"{similarity:.4f}"
        )

    else:

        st.warning("Please enter both texts.")