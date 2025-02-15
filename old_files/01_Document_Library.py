import streamlit as st
import requests
from datetime import datetime
import humanize
from PIL import Image
import fitz  # PyMuPDF
import io
import base64

def format_size(size_bytes: int) -> str:
    return humanize.naturalsize(size_bytes)

def format_date(date_str: str) -> str:
    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return date.strftime('%Y-%m-%d %H:%M:%S')

def get_document_list(session: requests.Session) -> list:
    """Fetch list of documents from the API."""
    response = session.get(f"{st.session_state.api_base_url}/documents/list")
    if response.status_code == 200:
        return response.json()
    return []

def get_document_thumbnail(file_type: str, doc_id: str) -> str:
    """Generate or get thumbnail for document."""
    # TODO: Implement actual thumbnail generation
    # For now, return placeholder based on file type
    return "📄"

def search_documents(session: requests.Session, query: str) -> list:
    """Search documents using vector-based retrieval."""
    try:
        response = session.get(
            f"{st.session_state.api_base_url}/documents/search",
            params={"query": query}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

def main():
    if not st.session_state.get("authenticated", False):
        st.error("Please log in to access this page.")
        return

    st.title("Document Library")

    # Search and Filter Section
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 Search documents...", placeholder="Enter keywords to search")
    with col2:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All", "Honeywell", "Tridium", "Johnson Controls", "General"]
        )

    # Sort options
    sort_option = st.selectbox(
        "Sort by",
        ["Upload Date (Newest)", "Upload Date (Oldest)", "Name (A-Z)", "Name (Z-A)"]
    )

    # Get documents
    documents = get_document_list(st.session_state.api_session)
    
    if not documents:
        st.info("No documents found in the library.")
        return

    # Apply filters
    if category_filter != "All":
        documents = [doc for doc in documents if doc.get('category', 'General') == category_filter]

    # Apply search if query exists
    if search_query:
        search_results = search_documents(st.session_state.api_session, search_query)
        if search_results:
            # Get document IDs from search results
            search_doc_ids = {doc['id'] for doc in search_results}
            documents = [doc for doc in documents if doc['id'] in search_doc_ids]

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
                # Card style using markdown and HTML
                st.markdown(f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 5px;
                    background-color: white;
                ">
                    <h3>{doc['filename']}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Document thumbnail
                thumbnail = get_document_thumbnail(doc['file_type'], doc['id'])
                st.markdown(f"<div style='text-align: center; font-size: 48px;'>{thumbnail}</div>", unsafe_allow_html=True)
                
                # Document details
                st.write(f"**Type:** {doc['file_type']}")
                st.write(f"**Size:** {format_size(doc['file_size'])}")
                st.write(f"**Uploaded:** {format_date(doc['created_at'])}")
                st.write(f"**Status:** {doc['status']}")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View", key=f"view_{doc['id']}"):
                        st.session_state.selected_document = doc['id']
                        # TODO: Implement document viewer
                with col2:
                    if st.button("Chat", key=f"chat_{doc['id']}"):
                        # TODO: Implement chat with document
                        pass

if __name__ == "__main__":
    main()
