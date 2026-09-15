import streamlit as st
from pypdf import PdfReader
import io
import zipfile
import re


# --------------------------------------------------
# Page setup
# --------------------------------------------------

st.set_page_config(
    page_title="Document Chunker",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Document Chunker")

st.write(
    "Upload a document, divide it into sentence-based chunks, "
    "explore the results, search for keywords, and download the chunks."
)


# --------------------------------------------------
# 1. Allows the user to upload a document
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a document",
    type=["pdf", "txt"]
)


if uploaded_file is not None:

    # --------------------------------------------------
    # Extract text from uploaded document
    # --------------------------------------------------

    if uploaded_file.type == "application/pdf":

        reader = PdfReader(uploaded_file)

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    else:

        bytes_data = uploaded_file.getvalue()
        text = bytes_data.decode("utf-8")


    st.success("Document uploaded successfully!")


    # --------------------------------------------------
    # Document information
    # --------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total Characters",
            len(text)
        )

    with col2:
        st.metric(
            "File Name",
            uploaded_file.name
        )


    # --------------------------------------------------
    # Preview original document
    # --------------------------------------------------

    with st.expander("👀 Preview Original Document"):

        st.text_area(
            "Extracted text",
            text,
            height=250
        )


    st.divider()


    # --------------------------------------------------
    # 2. Sentence-based chunking
    # --------------------------------------------------

    st.subheader("✂️ Sentence-Based Chunking")

    st.write(
        "The document will be divided into chunks while "
        "keeping whole sentences together."
    )


    # Split the document into sentences
    sentences = re.split(
        r'(?<=[.!?])\s+',
        text
    )


    # Remove empty sentences
    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


    # --------------------------------------------------
    # User chooses maximum sentences per chunk
    # --------------------------------------------------

    max_sentences = st.slider(
        "Maximum sentences per chunk",
        min_value=1,
        max_value=20,
        value=5,
        step=1
    )


    # --------------------------------------------------
    # Create chunks
    # --------------------------------------------------

    chunks = []

    for i in range(
        0,
        len(sentences),
        max_sentences
    ):

        sentence_group = sentences[
            i:i + max_sentences
        ]

        chunk = " ".join(
            sentence_group
        )

        chunks.append(chunk)


    # --------------------------------------------------
    # Chunk statistics
    # --------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Sentences",
            len(sentences)
        )

    with col2:
        st.metric(
            "Maximum Chunk Size",
            f"{max_sentences} sentences"
        )

    with col3:
        st.metric(
            "Total Chunks",
            len(chunks)
        )


    # --------------------------------------------------
    # 3. Saves each chunk to project directory
    # --------------------------------------------------

    for i, chunk in enumerate(chunks):

        with open(
            f"chunk_{i}.txt",
            "w",
            encoding="utf-8"
        ) as file:

            file.write(chunk)


    # --------------------------------------------------
    # 4. Reads first saved chunk into a variable
    # --------------------------------------------------

    with open(
        "chunk_0.txt",
        "r",
        encoding="utf-8"
    ) as file:

        first_chunk = file.read()


    # --------------------------------------------------
    # 5. Displays first saved chunk back to user
    # --------------------------------------------------

    st.divider()

    st.subheader("📌 First Saved Chunk")

    st.caption(
        f"Chunk 0 • {len(first_chunk)} characters"
    )

    st.text_area(
        "First chunk",
        first_chunk,
        height=250
    )


    # --------------------------------------------------
    # Display ALL chunking results
    # --------------------------------------------------

    st.divider()

    st.subheader("🧩 Chunking Results")

    st.write(
        f"The document contains **{len(sentences)} sentences** "
        f"and has been divided into **{len(chunks)} chunks**."
    )

    st.caption(
        "Click on any chunk below to see its content."
    )


    for i, chunk in enumerate(chunks):

        # Count sentences in this particular chunk
        chunk_sentences = sentences[
            i * max_sentences:
            (i + 1) * max_sentences
        ]

        with st.expander(
            f"Chunk {i} — "
            f"{len(chunk_sentences)} sentence(s) — "
            f"{len(chunk)} characters"
        ):

            st.write(chunk)


    # --------------------------------------------------
    # Interactive Chunk Explorer
    # --------------------------------------------------

    st.divider()

    st.subheader("🔎 Chunk Explorer")

    st.write(
        "Select any chunk to inspect it individually."
    )


    selected_chunk = st.selectbox(
        "Select a chunk",
        range(len(chunks)),
        format_func=lambda x: f"Chunk {x}"
    )


    selected_chunk_sentences = sentences[
        selected_chunk * max_sentences:
        (selected_chunk + 1) * max_sentences
    ]


    st.caption(
        f"Chunk {selected_chunk} • "
        f"{len(selected_chunk_sentences)} sentence(s) • "
        f"{len(chunks[selected_chunk])} characters"
    )


    st.text_area(
        "Selected chunk content",
        chunks[selected_chunk],
        height=300
    )


    # --------------------------------------------------
    # Keyword Search
    # --------------------------------------------------

    st.divider()

    st.subheader("🔍 Keyword Search")

    st.write(
        "Search for a word or phrase to find "
        "which chunks contain it."
    )


    keyword = st.text_input(
        "Search for a keyword",
        placeholder="e.g. contract, court, damages"
    )


    if keyword:

        matching_chunks = []


        # Search through every chunk
        for i, chunk in enumerate(chunks):

            if keyword.lower() in chunk.lower():

                matching_chunks.append(i)


        # --------------------------------------------------
        # Display keyword search results
        # --------------------------------------------------

        if matching_chunks:

            st.success(
                f'Found "{keyword}" in '
                f'{len(matching_chunks)} chunk(s).'
            )


            st.write(
                "**Found in:** "
                + ", ".join(
                    f"Chunk {i}"
                    for i in matching_chunks
                )
            )


            # Display every matching chunk
            for i in matching_chunks:

                matching_chunk_sentences = sentences[
                    i * max_sentences:
                    (i + 1) * max_sentences
                ]


                with st.expander(
                    f"📍 Chunk {i} — "
                    f"{len(matching_chunk_sentences)} sentence(s)"
                ):

                    st.write(chunks[i])


        else:

            st.warning(
                f'No chunks contain "{keyword}".'
            )


    # --------------------------------------------------
    # Download all chunks
    # --------------------------------------------------

    st.divider()

    st.subheader("💾 Save Chunk Files")

    st.write(
        "Download all chunks as separate text files "
        "inside one ZIP file."
    )


    # Create ZIP file in memory
    zip_buffer = io.BytesIO()


    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:

        for i, chunk in enumerate(chunks):

            zip_file.writestr(
                f"chunk_{i}.txt",
                chunk
            )


    # Download button
    st.download_button(
        label="📥 Download All Chunks",
        data=zip_buffer.getvalue(),
        file_name="document_chunks.zip",
        mime="application/zip"
    )