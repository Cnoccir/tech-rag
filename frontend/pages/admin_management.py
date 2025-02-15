# app/frontend/pages/admin_management.py
import streamlit as st
from app.frontend.utils import format_size, format_date
from app.frontend.api_client import APIClient

def get_status_color(status: str) -> str:
    """Get color code for document status"""
    colors = {
        'uploading': 'blue',
        'processing': 'orange',
        'completed': 'green',
        'failed': 'red',
        'deleted': 'gray'
    }
    return colors.get(status.lower(), 'default')

def show_admin_management():
    """Enhanced admin management view"""
    st.title("📑 Admin Document Management")

    if not st.session_state.get("is_admin", False):
        st.error("You are not authorized to view this page.")
        return

    # Document Upload Section with improved UI
    st.subheader("Upload Document")
    st.markdown("Upload and categorize documents for the technical library.")

    with st.container():
        st.markdown("""
        <div style="
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        ">
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "doc", "docx"],
            help="Supported formats: PDF, DOC, DOCX"
        )

        if uploaded_file:
            col1, col2 = st.columns([2, 1])
            with col1:
                category = st.selectbox(
                    "Select Category",
                    ["General", "Honeywell", "Tridium", "Johnson Controls"],
                    help="Choose the category that best fits your document."
                )
            with col2:
                if st.button("Upload", help="Click to upload the document", use_container_width=True):
                    try:
                        with st.spinner("Uploading & Processing..."):
                            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                            response = APIClient.post("documents/upload", files=files, data={"category": category})
                            st.success(f"Document '{uploaded_file.name}' uploaded successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    # Document Management Section with enhanced features
    st.subheader("Document Library Management")

    # Filters
    col1, col2 = st.columns([2, 1])
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            ["uploading", "processing", "completed", "failed", "deleted"],
            default=["completed", "processing", "uploading"]
        )
    with col2:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All", "Honeywell", "Tridium", "Johnson Controls", "General"]
        )

    try:
        # Fetch documents with filters
        params = {"include_deleted": True}
        if category_filter != "All":
            params["category"] = category_filter

        documents = APIClient.get("documents/list", params=params)

        if not documents:
            st.info("No documents found in the library.")
            return

        # Filter by status if selected
        if status_filter:
            documents = [doc for doc in documents if doc['status'].lower() in status_filter]

        # Display documents with enhanced UI
        for doc in documents:
            with st.expander(f"{doc['filename']} ({format_size(doc['file_size'])})"):
                # Document details in columns
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.markdown(f"**ID:** `{doc['id']}`")
                    st.markdown(f"**Owner:** {doc['created_by']}")
                    status_color = get_status_color(doc['status'])
                    st.markdown(
                        f"**Status:** <span style='color: {status_color}'>{doc['status'].upper()}</span>",
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown(f"**Category:** {doc['category']}")
                    st.markdown(f"**File Type:** {doc['file_type']}")
                    st.markdown(f"**Created:** {format_date(doc['created_at'])}")

                with col3:
                    # Document actions
                    if doc['status'] != 'deleted':
                        if st.button("Delete", key=f"del_{doc['id']}",
                                   help="Mark document as deleted",
                                   type="primary"):
                            try:
                                APIClient.delete(f"documents/{doc['id']}")
                                st.success("Document deleted successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Delete failed: {str(e)}")

                    # Additional metadata if available
                    if doc.get('error_message'):
                        st.error(f"Error: {doc['error_message']}")

                    # Processing progress if available
                    if doc.get('processed_chunks') and doc.get('total_chunks'):
                        progress = doc['processed_chunks'] / doc['total_chunks']
                        st.progress(progress, text="Processing Progress")

    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")
        if st.button("Retry", type="primary"):
            st.rerun()
