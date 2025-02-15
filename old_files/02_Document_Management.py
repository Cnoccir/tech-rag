import streamlit as st
import requests
from typing import Optional
import humanize
from datetime import datetime

# Utility functions

def format_size(size_bytes: int) -> str:
    return humanize.naturalsize(size_bytes)

def format_date(date_str: str) -> str:
    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return date.strftime('%Y-%m-%d %H:%M:%S')

def get_status_color(status: str) -> str:
    colors = {
        'uploading': 'blue',
        'processing': 'orange',
        'completed': 'green',
        'failed': 'red',
        'deleted': 'gray'
    }
    return colors.get(status, 'default')

# API interaction functions

def get_document_list(session: requests.Session) -> list:
    """Fetch list of documents from the API."""
    try:
        response = session.get(f"{st.session_state.api_base_url}/documents/list")
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch documents: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API server. Please ensure the backend is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    return []

def get_document_status(session: requests.Session, doc_id: str) -> Optional[dict]:
    """Fetch status of a specific document."""
    try:
        response = session.get(f"{st.session_state.api_base_url}/documents/status/{doc_id}")
        if response.status_code == 200:
            return response.json()
        st.error(f"Failed to fetch document status: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API server. Please ensure the backend is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    return None

def delete_document(session: requests.Session, doc_id: str) -> bool:
    """Delete a document."""
    try:
        response = session.delete(f"{st.session_state.api_base_url}/documents/{doc_id}")
        if response.status_code == 200:
            return True
        st.error(f"Failed to delete document: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API server. Please ensure the backend is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    return False

def upload_document(session: requests.Session, file, category: str) -> Optional[dict]:
    """Upload a document to the API."""
    try:
        files = {'file': file}
        data = {'category': category}
        response = session.post(f"{st.session_state.api_base_url}/documents/upload", files=files, data=data)
        if response.status_code == 200:
            return response.json()
        st.error(f"Upload failed: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API server. Please ensure the backend is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    return None

# Initialize session state variables if not present
if 'api_session' not in st.session_state:
    st.session_state.api_session = requests.Session()

if 'api_base_url' not in st.session_state:
    # Set your API base URL here.
    st.session_state.api_base_url = "http://localhost:8000/api/v1"

if 'selected_document' not in st.session_state:
    st.session_state.selected_document = None


def main():
    st.set_page_config(page_title="Tech RAG Document Management", layout="wide")
    st.title("📑 Tech RAG Document Management")
    
    # Upload section
    st.subheader("Upload Document")
    st.markdown("Upload your documents and categorize them for easy access.")
    uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "doc", "docx"], help="Supported formats: TXT, PDF, DOC, DOCX")
    
    if uploaded_file is not None:
        # Category selection
        category = st.selectbox(
            "Select Category",
            ["GENERAL", "HONEYWELL", "TRIDIUM", "JOHNSON_CONTROLS"],
            help="Choose the category that best fits your document."
        )
        
        if st.button("Upload", help="Click to upload the document"):
            with st.spinner("Uploading..."):
                if upload_document(st.session_state.api_session, uploaded_file, category):
                    st.success("Document uploaded successfully!")
                    st.rerun()
            
    # Document list section
    st.subheader("Document Library")
    st.markdown("Browse and manage your documents.")
    documents = get_document_list(st.session_state.api_session)

    if not documents:
        st.info("No documents found. Upload some documents to get started!")
    else:
        for doc in documents:
            with st.expander(f"{doc['filename']} ({format_size(doc['file_size'])})", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**Status:** {doc['status']}")
                    st.write(f"**Type:** {doc['file_type']}")
                    st.write(f"**Category:** {doc['category']}")
                with col2:
                    if doc.get('title'):
                        st.write(f"**Title:** {doc['title']}")
                    if doc.get('description'):
                        st.write(f"**Description:** {doc['description']}")
                    if doc.get('tags'):
                        st.write(f"**Tags:** {doc['tags']}")
                with col3:
                    if st.button("View & Chat", key=f"view_{doc['id']}", help="Open document and start a chat"):
                        st.session_state.selected_document = doc
                        st.rerun()
                    if st.button("Delete", key=f"del_{doc['id']}", help="Delete this document"):
                        if delete_document(st.session_state.api_session, doc['id']):
                            st.success("Document deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete document")

    # Chat and PDF Viewer
    if st.session_state.selected_document is not None:
        st.markdown("---")
        st.subheader(f"Chat & PDF Viewer: {st.session_state.selected_document['filename']}")
        # Chat interface (placeholder)
        st.write("Chat interface coming soon!")
        # PDF Viewer placeholder
        st.write("PDF Viewer coming soon!")

if __name__ == "__main__":
    main()
