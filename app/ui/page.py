import streamlit as st
import requests
import uuid

# -----------------------------------------------------------------------------
# Configuration & Setup
# -----------------------------------------------------------------------------
# Define your API endpoints here
API_BASE_URL = "http://localhost:8000"  # Update with your actual backend URL
UPLOAD_ENDPOINT = f"{API_BASE_URL}/api/v1/compliance/ingestion"
QUERY_ENDPOINT = f"{API_BASE_URL}/api/v1/compliance/query"

st.set_page_config(
    page_title="Regulatory Compliance Chat Assistant", page_icon="💬", layout="centered"
)
st.title("🏦 Regulatory AI Assistant")
st.write("🔍 Instant AI answers for corporate compliance and regulatory queries")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------------------------------------------
# Sidebar: PDF Upload (POST Request)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("📄 Document Upload")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        # Prevent re-uploading the same file unnecessarily
        if (
            "last_uploaded" not in st.session_state
            or st.session_state.last_uploaded != uploaded_file.name
        ):
            with st.spinner("Uploading and processing PDF..."):
                try:
                    # Prepare the file payload for the POST request
                    files = {
                        "pdf_file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    }
                    response = requests.post(UPLOAD_ENDPOINT, files=files)

                    if response.status_code == 200:
                        st.success(f"Successfully processed: {uploaded_file.name}")
                        st.session_state.last_uploaded = uploaded_file.name
                    else:
                        st.error(
                            f"Upload failed. Server responded with code: {response.status_code}"
                        )
                except requests.exceptions.RequestException as e:
                    st.error(
                        f"Connection error: Could not connect to the backend server.\n{e}"
                    )

# -----------------------------------------------------------------------------
# Main Chat Interface (POST Request)
# -----------------------------------------------------------------------------

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

st.sidebar.subheader("Previous Questions")

for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        if st.sidebar.button(msg["content"], key=f"q_{i}"):
            st.session_state.selected_question = msg["content"]

if "qa_cache" not in st.session_state:
    st.session_state.qa_cache = {}

# React to user input
if prompt := st.chat_input("Ask a compliance question..."):

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        with st.spinner("Searching regulations..."):
            try:
                payload = {
                    "query": prompt,
                    "thread_id": st.session_state.thread_id,
                }

                response = requests.post(QUERY_ENDPOINT, json=payload, timeout=60)

                if response.status_code == 200:
                    data = response.json()

                    answer = data.get("answer", "No answer available.")
                    citations = data.get("citations", [])

                    # Build response text
                    response_text = f"### Answer\n\n{answer}"

                    if citations:
                        response_text += "\n\n### Citations\n"

                        for idx, citation in enumerate(citations, start=1):
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
                        f"Server Error ({response.status_code})\n\n" f"{response.text}"
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
