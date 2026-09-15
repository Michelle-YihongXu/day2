import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader
import re
import json


# ==================================================
# SETUP
# ==================================================

load_dotenv()

client = OpenAI()

st.set_page_config(
    page_title="Legal RAG Reader",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Legal RAG Reader")

st.write(
    "Upload a legal document, ask a question, and retrieve "
    "the most relevant passages before generating an answer."
)


# ==================================================
# 1. UPLOAD DOCUMENT
# ==================================================

uploaded_file = st.file_uploader(
    "Upload a document",
    type=["pdf", "txt"]
)


# ==================================================
# 2. CLEAN TEXT
# ==================================================

def clean_text(text):

    # Replace multiple spaces with one space
    text = re.sub(
        r'[ \t]+',
        ' ',
        text
    )

    # Reduce excessive line breaks
    text = re.sub(
        r'\n+',
        '\n',
        text
    )

    return text.strip()


# ==================================================
# 3. SPLIT INTO SENTENCES
# ==================================================

def split_into_sentences(text):

    text = clean_text(text)

    sentences = re.split(
        r'(?<=[.!?])\s+',
        text
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    return sentences


# ==================================================
# 4. CREATE OVERLAPPING CHUNKS
# ==================================================

def create_chunks(
    sentences,
    chunk_size,
    overlap
):

    chunks = []

    step = chunk_size - overlap

    if step <= 0:
        step = 1

    for i in range(
        0,
        len(sentences),
        step
    ):

        chunk_sentences = sentences[
            i:i + chunk_size
        ]

        if not chunk_sentences:
            break

        chunk = " ".join(
            chunk_sentences
        )

        chunks.append(chunk)

        if i + chunk_size >= len(sentences):
            break

    return chunks


# ==================================================
# 5. RETRIEVE TOP CHUNKS
# ==================================================

def retrieve_chunks(
    question,
    chunks,
    top_k
):

    numbered_chunks = ""

    for i, chunk in enumerate(
        chunks,
        start=1
    ):

        numbered_chunks += f"""

--- CHUNK {i} ---

{chunk}

"""

    prompt = f"""
You are performing retrieval for legal research.

You have a document divided into numbered chunks.

USER QUESTION:

{question}


Your task is to identify the {top_k} chunks that are
most useful for answering the question.

IMPORTANT:

Do not simply search for matching words.

Consider:

1. Direct answers to the question.
2. Statements of the author's position.
3. Conclusions.
4. Qualifications or exceptions.
5. Reasoning supporting the author's position.
6. Passages that contradict or complicate another passage.
7. Context necessary to interpret the author's meaning.

For questions asking whether an author agrees with a proposition,
prioritise passages where the author explicitly evaluates,
balances, qualifies, accepts, or rejects that proposition.

Return ONLY the chunk numbers.

Example:

4, 17, 31, 42, 58

Do not provide explanations.


DOCUMENT:

{numbered_chunks}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = (
        response
        .choices[0]
        .message
        .content
        .strip()
    )

    numbers = re.findall(
        r'\d+',
        result
    )

    chunk_numbers = []

    for number in numbers:

        number = int(number)

        if (
            1 <= number <= len(chunks)
            and number not in chunk_numbers
        ):

            chunk_numbers.append(
                number
            )

    chunk_numbers = (
        chunk_numbers[:top_k]
    )

    relevant_chunks = [
        chunks[number - 1]
        for number in chunk_numbers
    ]

    return (
        relevant_chunks,
        chunk_numbers
    )


# ==================================================
# 6. ANALYSE RETRIEVED SOURCES
# ==================================================

def analyse_sources(
    question,
    relevant_chunks,
    chunk_numbers
):

    source_text = ""

    for number, chunk in zip(
        chunk_numbers,
        relevant_chunks
    ):

        source_text += f"""

--- CHUNK {number} ---

{chunk}

"""

    prompt = f"""
You are evaluating evidence retrieved from a legal document.

QUESTION:

{question}


RETRIEVED PASSAGES:

{source_text}


For each chunk, determine:

1. How relevant it is to the question.
2. Whether it contains:
   - an explicit statement;
   - supporting reasoning;
   - a qualification;
   - an exception;
   - a conclusion;
   - contextual information.
3. Why it matters to answering the question.

Return valid JSON ONLY.

Use this structure:

[
  {{
    "chunk": 4,
    "relevance": "High",
    "type": "Explicit statement",
    "reason": "The author directly addresses..."
  }}
]

Do not include any text outside the JSON.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = (
        response
        .choices[0]
        .message
        .content
        .strip()
    )

    # Remove markdown code fences if GPT adds them
    result = result.replace(
        "```json",
        ""
    ).replace(
        "```",
        ""
    ).strip()

    try:

        analysis = json.loads(
            result
        )

    except json.JSONDecodeError:

        analysis = []

    return analysis


# ==================================================
# 7. GENERATE LEGAL ANSWER
# ==================================================

def answer_question(
    question,
    relevant_chunks,
    chunk_numbers
):

    source_text = ""

    for number, chunk in zip(
        chunk_numbers,
        relevant_chunks
    ):

        source_text += f"""

--- SOURCE CHUNK {number} ---

{chunk}

"""

    prompt = f"""
You are a careful legal research assistant.

Answer the user's question using ONLY the retrieved
document passages below.

QUESTION:

{question}


SOURCES:

{source_text}


STRICT RULES:

1. Do not use outside knowledge.

2. Every substantive proposition about the document
   or author's position must be supported by a
   [Chunk X] citation.

3. Distinguish carefully between:

   EXPLICIT:
   Something the author directly states.

   INFERENCE:
   Something that can reasonably be inferred from
   the author's reasoning but is not directly stated.

4. Never convert words such as:

   "balance"
   "important"
   "competing"
   "greater weight"
   "consider"

   into a stronger claim such as:

   "equal importance"

   unless the author actually says this.

5. Pay attention to qualifications, exceptions,
   different legal contexts, and changes in emphasis.

6. If different passages point in different directions,
   explain the tension rather than hiding it.

7. If the evidence cannot establish the proposition
   asked by the user, say so clearly.

8. Do not invent quotations.

9. Cite the relevant source immediately after the
   proposition it supports.


OUTPUT FORMAT:


## English Answer

### Short Answer

Give a direct answer to the question in 1-3 sentences.


### Evidence and Reasoning

Explain the relevant evidence.

Clearly indicate when something is:

**Explicit statement:**

or

**Reasonable inference:**

Use [Chunk X] citations throughout.


### Qualification

Explain any important limitation, exception,
ambiguity, or competing interpretation.


## 中文翻译

Provide a faithful Chinese translation of the entire
English answer.

Preserve all [Chunk X] citations.

Preserve the distinction between:

明确陈述（Explicit statement）

and

合理推论（Reasonable inference）

Do not introduce any new information in Chinese.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


# ==================================================
# 8. PROCESS DOCUMENT
# ==================================================

if uploaded_file is not None:

    # ----------------------------------------------
    # PDF
    # ----------------------------------------------

    if uploaded_file.type == "application/pdf":

        reader = PdfReader(
            uploaded_file
        )

        text = ""

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            page_text = (
                page.extract_text()
            )

            if page_text:

                text += (
                    page_text + "\n"
                )


    # ----------------------------------------------
    # TXT
    # ----------------------------------------------

    else:

        text = (
            uploaded_file
            .read()
            .decode("utf-8")
        )


    # ==================================================
    # 9. CHUNK SETTINGS
    # ==================================================

    st.subheader(
        "Document Processing"
    )

    col1, col2, col3 = st.columns(3)


    with col1:

        chunk_size = st.slider(
            "Sentences per chunk",
            min_value=3,
            max_value=15,
            value=6
        )


    with col2:

        overlap = st.slider(
            "Sentence overlap",
            min_value=0,
            max_value=5,
            value=2
        )


    with col3:

        top_k = st.slider(
            "Number of sources to retrieve",
            min_value=1,
            max_value=8,
            value=5
        )


    # Prevent invalid overlap
    if overlap >= chunk_size:

        st.warning(
            "Overlap must be smaller than chunk size."
        )

        st.stop()


    # ==================================================
    # 10. CREATE CHUNKS
    # ==================================================

    sentences = split_into_sentences(
        text
    )

    chunks = create_chunks(
        sentences,
        chunk_size,
        overlap
    )


    st.success(
        f"Document processed into "
        f"{len(chunks)} overlapping chunks."
    )

    st.caption(
        f"{len(sentences)} sentences detected."
    )


    # ==================================================
    # 11. VIEW CHUNKS
    # ==================================================

    with st.expander(
        "View all document chunks"
    ):

        for i, chunk in enumerate(
            chunks,
            start=1
        ):

            st.markdown(
                f"### Chunk {i}"
            )

            st.write(
                chunk
            )


    # ==================================================
    # 12. QUESTION
    # ==================================================

    st.divider()

    st.subheader(
        "Ask the document"
    )

    question = st.text_area(
        "Your question",
        height=100,
        placeholder=(
            "Ask a question about "
            "the document..."
        )
    )


    # ==================================================
    # 13. RUN RAG
    # ==================================================

    if st.button(
        "Search and Answer",
        type="primary"
    ):

        if not question:

            st.warning(
                "Please enter a question."
            )

        else:

            # ==========================================
            # STEP 1 — RETRIEVAL
            # ==========================================

            with st.spinner(
                "Step 1/3 — Retrieving relevant passages..."
            ):

                (
                    relevant_chunks,
                    chunk_numbers
                ) = retrieve_chunks(
                    question,
                    chunks,
                    top_k
                )


            if not relevant_chunks:

                st.error(
                    "No relevant passages could be retrieved."
                )

                st.stop()


            # ==========================================
            # STEP 2 — SOURCE ANALYSIS
            # ==========================================

            with st.spinner(
                "Step 2/3 — Evaluating the evidence..."
            ):

                source_analysis = analyse_sources(
                    question,
                    relevant_chunks,
                    chunk_numbers
                )


            # ==========================================
            # STEP 3 — ANSWER
            # ==========================================

            with st.spinner(
                "Step 3/3 — Generating grounded answer..."
            ):

                answer = answer_question(
                    question,
                    relevant_chunks,
                    chunk_numbers
                )


            # ==================================================
            # 14. ANSWER
            # ==================================================

            st.divider()

            st.header(
                "Answer"
            )

            st.markdown(
                answer
            )


            # ==================================================
            # 15. RETRIEVAL INFORMATION
            # ==================================================

            st.divider()

            st.header(
                "Retrieved Evidence"
            )

            st.write(
                "Retrieved chunks: "
                + ", ".join(
                    str(number)
                    for number
                    in chunk_numbers
                )
            )


            # ==================================================
            # 16. SHOW SOURCE ANALYSIS
            # ==================================================

            if source_analysis:

                st.subheader(
                    "Why these passages were retrieved"
                )

                for item in source_analysis:

                    chunk_number = (
                        item.get(
                            "chunk",
                            "?"
                        )
                    )

                    relevance = (
                        item.get(
                            "relevance",
                            "Unknown"
                        )
                    )

                    evidence_type = (
                        item.get(
                            "type",
                            "Unknown"
                        )
                    )

                    reason = (
                        item.get(
                            "reason",
                            ""
                        )
                    )

                    st.markdown(
                        f"**Chunk {chunk_number}** "
                        f"— {relevance}"
                    )

                    st.write(
                        f"Evidence type: "
                        f"{evidence_type}"
                    )

                    st.write(
                        reason
                    )


            # ==================================================
            # 17. SHOW ORIGINAL SOURCES
            # ==================================================

            st.subheader(
                "Original Source Passages"
            )

            for rank, (
                number,
                chunk
            ) in enumerate(
                zip(
                    chunk_numbers,
                    relevant_chunks
                ),
                start=1
            ):

                with st.expander(
                    f"Source {rank} — Chunk {number}",
                    expanded=(
                        rank <= 2
                    )
                ):

                    st.write(
                        chunk
                    )


            # ==================================================
            # 18. EXPLAIN PIPELINE
            # ==================================================

            st.divider()

            st.caption(
                "Pipeline: Document → overlapping chunks → "
                "GPT-4o retrieval → evidence evaluation → "
                "grounded answer → bilingual output."
            )