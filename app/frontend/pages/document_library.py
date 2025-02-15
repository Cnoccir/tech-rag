import streamlit as st
import requests
from app.frontend.utils import (
    format_size,
    format_date,
    get_documents,
    search_documents
)

def show_document_library():
    st.title("Document Library")

    if "api_session" not in st.session_state:
        st.session_state.api_session = requests.Session()

    token = st.session_state.get("access_token", "")
    base_url = st.session_state.get("api_base_url", "")

    # Update the session's headers with token
    st.session_state.api_session.headers.update({"Authorization": f"Bearer {token}"})

    search_query = st.text_input("Search documents", "")
    category_filter = st.selectbox(
        "Filter by Category",
        ["All", "Honeywell", "Tridium", "Johnson Controls", "General"]
    )
    cat = None if category_filter == "All" else category_filter

    if st.button("Search"):
        try:
            documents = search_documents(
                st.session_state.api_session,
                base_url,
                query=search_query,
                category_filter=cat
            )
        except Exception as e:
            st.error(f"Search request failed: {e}")
            documents = []
    else:
        try:
            documents = get_documents(
                st.session_state.api_session,
                base_url,
                category_filter=cat,
                include_deleted=False
            )
        except Exception as e:
            st.error(f"Failed to fetch documents: {e}")
            documents = []

    if not documents:
        st.info("No documents found.")
        return

    for doc in documents:
        with st.expander(f"{doc['filename']} ({format_size(doc['file_size'])})"):
            st.write(f"**ID:** {doc['id']}")
            st.write(f"**Status:** {doc['status']}")
            st.write(f"**Category:** {doc['category']}")
            st.write(f"**Uploaded:** {format_date(doc['created_at'])}")

            if st.button("Chat with Document", key=f"chat_{doc['id']}"):
                st.session_state["selected_document_id"] = doc["id"]
                st.session_state["selected_document_name"] = doc["filename"]
                st.success(f"Selected '{doc['filename']}' for chat. Switch to 'Chat' page.")
