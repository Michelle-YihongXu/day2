import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import hashlib
import os
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

os.environ["CHROMA_OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]

CHUNKS_FOLDER = "Chunks - Mallard v Homes Victoria [2025] 339 - Summary of Judgment"

@st.cache_resource
def get_collection():
    client = chromadb.PersistentClient(path="./my_chroma_db")

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        model_name="text-embedding-3-large",
    )

    collection = client.get_or_create_collection(
        name="knowledge_base",
        embedding_function=openai_ef,
    )

    # ingest once, silently — upsert means re-runs are safe
    folder = Path(CHUNKS_FOLDER)
    if folder.exists():
        files = sorted(folder.glob("*.txt")) + sorted(folder.glob("*.md"))
        documents, metadatas, ids = [], [], []
        for file in files:
            text = file.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                documents.append(text)
                metadatas.append({"source": "Mallard v Homes Victoria [2025] 339", "filename": file.name})
                ids.append(hashlib.md5(file.name.encode()).hexdigest())
        if documents:
            collection.upsert(documents=documents, metadatas=metadatas, ids=ids)

    return collection

collection = get_collection()

# --- Search UI ---
st.title("Mallard v Homes Victoria — Search")
query = st.text_input("Search query")
n_results = 1

# Add chunk to prompt using prompt templating, to provide a RAG response
client = OpenAI()

if st.button("Search") and query:
    results = collection.query(query_texts=[query], n_results=n_results)
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        with st.container(border=True):
            st.write(doc)
            st.caption(f"source: {meta.get('filename')} · distance: {dist:.3f}")

    # Use the retrieved chunk(s) as context for a RAG response
    context = "\n\n---\n\n".join(results["documents"][0])

    prompt = f"""You are a legal research assistant. Answer the question using only the context below.
    If the context doesn't contain the answer, say so — do not make anything up.

    Context:
    {context}

    Question: {query}

    Answer:"""

    with st.spinner("Generating response..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

    st.subheader("Answer")
    st.write(response.choices[0].message.content)
