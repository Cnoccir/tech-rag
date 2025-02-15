import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from frontend.api_client import APIClient

def show_chat():
    """Chat interface view"""
    st.title("Chat with Document")

    if "selected_document_id" not in st.session_state:
        st.info("No document selected. Go to 'Document Library' first.")
        return

    doc_id = st.session_state["selected_document_id"]
    doc_name = st.session_state["selected_document_name"]
    st.write(f"**Document ID:** {doc_id}")
    st.write(f"**Document Name:** {doc_name}")

    try:
        # Get document preview URL
        preview_response = APIClient.get(f"documents/{doc_id}/download_url")
        presigned_url = preview_response.get("url", "")

        if presigned_url:
            st.subheader("PDF Viewer")
            pdf_viewer(presigned_url, width="100%", height=800, render_text=True)

        # Chat interface
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        user_input = st.text_input("Ask a question about this document:")
        if st.button("Send") and user_input.strip():
            # Add user message to history
            st.session_state["chat_history"].append({"role": "user", "content": user_input})

            # Get AI response
            response = APIClient.post("chat/ask", json={
                "document_id": doc_id,
                "query": user_input,
                "history": st.session_state["chat_history"]
            })

            # Add AI response to history
            st.session_state["chat_history"].append({
                "role": "assistant",
                "content": response.get("response", "")
            })

        # Display chat history
        st.write("---")
        for msg in st.session_state["chat_history"]:
            role = "User" if msg["role"] == "user" else "Assistant"
            st.markdown(f"**{role}:** {msg['content']}")

    except Exception as e:
        st.error(f"Error: {str(e)}")
