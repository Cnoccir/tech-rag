# app/frontend/pages/document_library.py
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

def get_document_thumbnail(file_type: str) -> str:
    """Get document emoji based on file type"""
    icons = {
        'application/pdf': '📄',
        'application/msword': '📝',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '📝',
        'text/plain': '📋'
    }
    return icons.get(file_type, '📄')

def show_document_library():
    """Enhanced document library view"""
    st.title("Document Library")

    # Search and Filter Section with improved layout
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search_query = st.text_input("🔍 Search documents...",
                                    placeholder="Enter keywords to search")
    with col2:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All", "Honeywell", "Tridium", "Johnson Controls", "General"]
        )
    with col3:
        sort_option = st.selectbox(
            "Sort by",
            ["Upload Date (Newest)", "Upload Date (Oldest)",
             "Name (A-Z)", "Name (Z-A)"]
        )

    # Upload section in a card
    with st.expander("📤 Upload New Document", expanded=False):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "doc", "docx"],
            help="Supported formats: PDF, DOC, DOCX"
        )
        if uploaded_file:
            category = st.selectbox(
                "Select Category",
                ["General", "Honeywell", "Tridium", "Johnson Controls"]
            )
            if st.button("Upload", help="Click to upload the document"):
                try:
                    with st.spinner("Uploading & Processing..."):
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        APIClient.post("documents/upload", files=files, data={"category": category})
                        st.success("Document uploaded successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Upload failed: {str(e)}")

    try:
        # Fetch and filter documents
        cat = None if category_filter == "All" else category_filter
        if search_query:
            documents = APIClient.get("documents/search", params={
                "query": search_query,
                "category": cat
            })
        else:
            documents = APIClient.get("documents/list", params={
                "category": cat,
                "include_deleted": False
            })

        if not documents:
            st.info("No documents found.")
            return

        # Apply sorting
        if sort_option == "Upload Date (Newest)":
            documents.sort(key=lambda x: x['created_at'], reverse=True)
        elif sort_option == "Upload Date (Oldest)":
            documents.sort(key=lambda x: x['created_at'])
        elif sort_option == "Name (A-Z)":
            documents.sort(key=lambda x: x['filename'].lower())
        elif sort_option == "Name (Z-A)":
            documents.sort(key=lambda x: x['filename'].lower(), reverse=True)

        # Display documents in a grid
        cols = st.columns(3)
        for idx, doc in enumerate(documents):
            with cols[idx % 3]:
                with st.container():
                    # Card style using markdown
                    st.markdown(f"""
                    <div style="
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 5px;
                        background-color: white;
                    ">
                        <h3 style="margin: 0; padding-bottom: 10px;">{doc['filename']}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Document icon and details
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        thumbnail = get_document_thumbnail(doc['file_type'])
                        st.markdown(f"<div style='text-align: center; font-size: 48px;'>{thumbnail}</div>",
                                  unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"**Size:** {format_size(doc['file_size'])}")
                        st.markdown(f"**Uploaded:** {format_date(doc['created_at'])}")
                        status_color = get_status_color(doc['status'])
                        st.markdown(f"**Status:** <span style='color: {status_color}'>{doc['status']}</span>",
                                  unsafe_allow_html=True)

                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("View", key=f"view_{doc['id']}",
                                   help="Open document viewer"):
                            # Store document info in session state
                            st.session_state["selected_document_id"] = doc["id"]
                            st.session_state["selected_document_name"] = doc["filename"]
                            # TODO: Implement document viewer
                            st.info("Document viewer coming soon!")
                    with col2:
                        if st.button("Chat", key=f"chat_{doc['id']}",
                                   help="Start chat with this document"):
                            st.session_state["selected_document_id"] = doc["id"]
                            st.session_state["selected_document_name"] = doc["filename"]
                            st.success(f"Selected '{doc['filename']}' for chat. Switch to 'Chat' page.")

    except Exception as e:
        st.error(f"Error: {str(e)}")
