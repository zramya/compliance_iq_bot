import streamlit as st
import requests

# -----------------------------------------------------------------------------
# Configuration & Setup
# -----------------------------------------------------------------------------
# Define your API endpoints here
API_BASE_URL = "http://localhost:8000"  # Update with your actual backend URL
UPLOAD_ENDPOINT = f"{API_BASE_URL}/api/v1/compliance/ingestion"
QUERY_ENDPOINT = f"{API_BASE_URL}/query"

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
# Main Chat Interface (GET Request)
# -----------------------------------------------------------------------------
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask something about your PDF..."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        with st.spinner("Searching document..."):
            try:
                # Pass the user query as a URL parameter for the GET request
                params = {"search": prompt}
                response = requests.get(QUERY_ENDPOINT, params=params)

                if response.status_code == 200:
                    # Parse the JSON response. Adjust the key based on your API schema
                    data = response.json()
                    answer = data.get(
                        "answer",
                        data.get("response", "No answer found in the server response."),
                    )

                    message_placeholder.markdown(answer)
                    # Add assistant response to chat history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                else:
                    error_msg = (
                        f"Error: Server returned status code {response.status_code}"
                    )
                    message_placeholder.markdown(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

            except requests.exceptions.RequestException as e:
                error_msg = (
                    f"Connection error: Could not connect to the backend server.\n{e}"
                )
                message_placeholder.markdown(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
