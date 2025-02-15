import streamlit as st
import requests
from streamlit_pdf_viewer import pdf_viewer

def show_chat():
    st.title("Chat with Document")

    if "selected_document_id" not in st.session_state:
        st.info("No document selected. Go to 'Document Library' first.")
        return

    doc_id = st.session_state["selected_document_id"]
    doc_name = st.session_state["selected_document_name"]
    st.write(f"**Document ID:** {doc_id}")
    st.write(f"**Document Name:** {doc_name}")

    if "api_session" not in st.session_state:
        st.session_state.api_session = requests.Session()
    token = st.session_state.get("access_token", "")
    base_url = st.session_state.get("api_base_url", "")
    st.session_state.api_session.headers.update({"Authorization": f"Bearer {token}"})

    # Attempt to fetch presigned URL from backend
    try:
        resp = st.session_state.api_session.get(f"{base_url}/documents/{doc_id}/download_url")
        if resp.status_code == 200:
            presigned_data = resp.json()
            presigned_url = presigned_data.get("url", "")
        else:
            presigned_url = ""
            st.warning(f"Failed to fetch download URL: {resp.text}")
    except Exception as e:
        st.error(f"Error fetching presigned URL: {e}")
        presigned_url = ""

    # Show PDF viewer if we got a URL
    if presigned_url:
        st.subheader("PDF Viewer")
        pdf_viewer(
            input=presigned_url,
            width="100%",
            height=800,
            render_text=True
        )

    # Simple Q&A chat
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_input = st.text_input("Ask a question about this document:")
    if st.button("Send"):
        if user_input.strip():
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            # call your RAG endpoint
            answer = ask_rag_endpoint(doc_id, user_input, st.session_state["chat_history"])
            st.session_state["chat_history"].append({"role": "assistant", "content": answer})

    st.write("---")
    for msg in st.session_state["chat_history"]:
        role = "User" if msg["role"] == "user" else "Assistant"
        st.markdown(f"**{role}:** {msg['content']}")

def ask_rag_endpoint(doc_id: str, query: str, history):
    """
    Example calling a backend RAG chat route /chat/ask
    POST body: { "document_id": doc_id, "query": query, "history": ... }
    """
    token = st.session_state.get("access_token", "")
    base_url = st.session_state.get("api_base_url", "")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "document_id": doc_id,
        "query": query,
        "history": history
    }
    try:
        r = st.session_state.api_session.post(f"{base_url}/chat/ask", json=payload, headers=headers)
        if r.status_code == 200:
            data = r.json()
            return data.get("response", "")
        else:
            return f"Error from server: {r.status_code} {r.text}"
    except Exception as e:
        return f"Chat request failed: {e}"
