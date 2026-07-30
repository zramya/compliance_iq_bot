import streamlit as st
import requests
import uuid
import re

# -----------------------------------------------------------------------------
# Configuration & Setup
# -----------------------------------------------------------------------------

API_BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{API_BASE_URL}/api/v1/compliance/ingestion"
QUERY_ENDPOINT = f"{API_BASE_URL}/api/v1/compliance/query"


st.set_page_config(
    page_title="Regulatory Compliance Chat Assistant",
    page_icon="💬",
    layout="centered",
)


st.title("🏦 Regulatory AI Assistant")
st.write("🔍 Instant AI answers for corporate compliance and regulatory queries")

# -----------------------------------------------------------------------------
# Session State
# -----------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "qa_cache" not in st.session_state:
    st.session_state.qa_cache = {}


# -----------------------------------------------------------------------------
# Personal Conversation Handler
# -----------------------------------------------------------------------------


def handle_personal_conversation(message: str):
    """
    Handle non-regulatory conversation without backend calls.
    """

    text = message.strip()
    lower_text = text.lower()

    # -------------------------
    # Capture user name
    # -------------------------

    name_patterns = [
        r"my name is (.+)",
        r"i am (.+)",
        r"i'm (.+)",
        r"call me (.+)",
    ]

    for pattern in name_patterns:

        match = re.search(
            pattern,
            lower_text,
        )

        if match:

            name = match.group(1).strip().title()

            st.session_state.user_name = name

            return (
                f"Hi {name}. How can I help you with "
                "RBI, SEBI, Basel III, or banking "
                "regulatory compliance today?"
            )

    # -------------------------
    # Greetings
    # -------------------------

    greetings = [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good evening",
    ]

    if lower_text in greetings:

        if st.session_state.user_name:

            return (
                f"Hi {st.session_state.user_name}. "
                "How can I help you with RBI, SEBI, "
                "Basel III, or banking regulatory "
                "compliance today?"
            )

        return (
            "Hello. Please share your RBI, SEBI, Basel III, "
            "or banking regulatory compliance question."
        )

    # -------------------------
    # User identity question
    # -------------------------

    if "who am i" in lower_text:

        if st.session_state.user_name:

            return f"You are {st.session_state.user_name}."

        return "You haven't shared your name in this conversation."

    # -------------------------
    # Compliments
    # -------------------------

    compliments = [
        "thanks",
        "thank you",
        "great",
        "good",
        "awesome",
        "excellent",
        "nice",
        "perfect",
        "well done",
    ]

    if lower_text in compliments:

        if st.session_state.user_name:

            return (
                f"Thank you, {st.session_state.user_name}. "
                "Please share your RBI, SEBI, Basel III, "
                "or banking regulatory compliance question."
            )

        return (
            "Thank you. Please share your RBI, SEBI, Basel III, "
            "or banking regulatory compliance question."
        )

    return None


# -----------------------------------------------------------------------------
# Sidebar: PDF Upload
# -----------------------------------------------------------------------------

with st.sidebar:

    st.header("📄 Document Upload")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
    )

    if uploaded_file is not None:

        if (
            "last_uploaded" not in st.session_state
            or st.session_state.last_uploaded != uploaded_file.name
        ):

            with st.spinner("Uploading and processing PDF..."):

                try:

                    files = {
                        "pdf_file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    }

                    response = requests.post(
                        UPLOAD_ENDPOINT,
                        files=files,
                    )

                    if response.status_code == 200:

                        st.success(f"Successfully processed: " f"{uploaded_file.name}")

                        st.session_state.last_uploaded = uploaded_file.name

                    else:

                        st.error(f"Upload failed. " f"Code: {response.status_code}")

                except requests.exceptions.RequestException as e:

                    st.error(f"Connection error:\n{e}")


# -----------------------------------------------------------------------------
# Display Chat History
# -----------------------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# -----------------------------------------------------------------------------
# Previous Questions
# -----------------------------------------------------------------------------

st.sidebar.subheader("Previous Questions")


for i, msg in enumerate(st.session_state.messages):

    if msg["role"] == "user":

        if st.sidebar.button(
            msg["content"],
            key=f"q_{i}",
        ):

            st.session_state.selected_question = msg["content"]
# -----------------------------------------------------------------------------
# Main Chat Interface
# -----------------------------------------------------------------------------

if prompt := st.chat_input("Ask a compliance question..."):

    personal_response = handle_personal_conversation(prompt)

    # -------------------------------------------------------------------------
    # Handle Personal Conversation
    # No backend call, no retrieval tools
    # -------------------------------------------------------------------------

    if personal_response:

        with st.chat_message("user"):

            st.markdown(prompt)

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("assistant"):

            st.markdown(personal_response)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": personal_response,
            }
        )

        st.stop()

    # -------------------------------------------------------------------------
    # Regulatory Questions
    # Send to backend agent
    # -------------------------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(prompt)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("assistant"):

        message_placeholder = st.empty()

        with st.spinner("Searching regulations..."):

            try:

                payload = {
                    "query": prompt,
                    "thread_id": st.session_state.thread_id,
                    "chat_history": st.session_state.messages,
                }

                response = requests.post(
                    QUERY_ENDPOINT,
                    json=payload,
                    timeout=60,
                )
                st.session_state.messages.append({"role": "user", "content": prompt})

                if response.status_code == 200:

                    data = response.json()

                    answer = data.get(
                        "answer",
                        "No answer available.",
                    )

                    citations = data.get(
                        "citations",
                        [],
                    )

                    response_text = f"### Answer\n\n{answer}"

                    if citations:

                        response_text += "\n\n### Citations\n"

                        for idx, citation in enumerate(
                            citations,
                            start=1,
                        ):

                            response_text += f"\n{idx}. {citation}"

                    st.session_state.qa_cache[prompt] = response_text

                    message_placeholder.markdown(response_text)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response_text,
                        }
                    )

                else:

                    error_msg = (
                        f"Server Error "
                        f"({response.status_code})\n\n"
                        f"{response.text}"
                    )

                    message_placeholder.markdown(error_msg)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_msg,
                        }
                    )

            except requests.exceptions.RequestException as e:

                error_msg = f"Connection error:\n\n{e}"

                message_placeholder.markdown(error_msg)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_msg,
                    }
                )
