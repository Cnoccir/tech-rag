import streamlit as st
import requests
from app.frontend.utils import (
    upload_document,
    get_documents,
    format_size,
    format_date
)

def show_admin_management():
    st.title("Admin Document Management")

    if not st.session_state.get("is_admin", False):
        st.error("You are not authorized to view this page.")
        return

    if "api_session" not in st.session_state:
        st.session_state.api_session = requests.Session()

    token = st.session_state.get("access_token", "")
    base_url = st.session_state.get("api_base_url", "")
    st.session_state.api_session.headers.update({"Authorization": f"Bearer {token}"})

    st.subheader("Upload New Document")
    uploaded_file = st.file_uploader("Choose file", type=["pdf", "doc", "docx"])
    if uploaded_file:
        category = st.selectbox("Category", ["General", "Honeywell", "Tridium", "Johnson_Controls"])
        if st.button("Upload"):
            with st.spinner("Uploading..."):
                success = upload_document(st.session_state.api_session, base_url, uploaded_file, category)
                if success:
                    st.success("Document uploaded & processed.")
                    st.experimental_rerun()
                else:
                    st.error("Upload failed.")

    st.subheader("All Documents")
    try:
        documents = get_documents(st.session_state.api_session, base_url, category_filter=None, include_deleted=True)
    except Exception as e:
        st.error(f"Failed to list documents: {e}")
        return

    if not documents:
        st.info("No documents found.")
        return

    for doc in documents:
        with st.expander(f"{doc['filename']} ({format_size(doc['file_size'])})"):
            st.write(f"**ID:** {doc['id']}")
            st.write(f"**Owner:** {doc['created_by']}")
            st.write(f"**Status:** {doc['status']}")
            st.write(f"**Category:** {doc['category']}")
            st.write(f"**Created:** {format_date(doc['created_at'])}")

            if st.button("Delete", key=f"del_{doc['id']}"):
                resp = st.session_state.api_session.delete(f"{base_url}/documents/{doc['id']}")
                if resp.status_code == 200:
                    st.success("Document deleted.")
                    st.experimental_rerun()
                else:
                    st.error(f"Delete failed: {resp.text}")
