import streamlit as st
import requests
import time
from typing import Optional
import humanize
from datetime import datetime

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

def get_document_list(session: requests.Session) -> list:
    """Fetch list of documents from the API."""
    response = session.get(f"{st.session_state.api_base_url}/documents/list")
    if response.status_code == 200:
        return response.json()
    return []

def get_document_status(session: requests.Session, doc_id: str) -> Optional[dict]:
    """Fetch status of a specific document."""
    response = session.get(f"{st.session_state.api_base_url}/documents/status/{doc_id}")
    if response.status_code == 200:
        return response.json()
    return None

def delete_document(session: requests.Session, doc_id: str) -> bool:
    """Delete a document."""
    response = session.delete(f"{st.session_state.api_base_url}/documents/{doc_id}")
    return response.status_code == 200

def upload_document(session: requests.Session, file) -> Optional[dict]:
    """Upload a document to the API."""
    files = {'file': file}
    response = session.post(f"{st.session_state.api_base_url}/documents/upload", files=files)
    if response.status_code == 200:
        return response.json()
    st.error(f"Upload failed: {response.text}")
    return None

def main():
    st.title("📑 Document Management")
    
    if "user" not in st.session_state:
        st.warning("Please log in first")
        st.stop()
    
    # Create tabs for different sections
    tab1, tab2 = st.tabs(["Upload Document", "Document List"])
    
    with tab1:
        st.header("Upload New Document")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'txt', 'doc', 'docx'],
            help="Upload a PDF, TXT, DOC, or DOCX file"
        )
        
        if uploaded_file:
            if st.button("Process Document"):
                with st.spinner("Uploading document..."):
                    doc = upload_document(st.session_state.api_session, uploaded_file)
                    
                if doc:
                    st.success(f"Document '{doc['filename']}' uploaded successfully!")
                    
                    # Create a progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Poll for document status
                    while True:
                        doc_status = get_document_status(st.session_state.api_session, doc['id'])
                        
                        if not doc_status:
                            st.error("Failed to get document status")
                            break
                            
                        status = doc_status['status']
                        progress = 0
                        
                        if status == 'completed':
                            progress = 1.0
                            status_text.success("Processing completed!")
                            break
                        elif status == 'failed':
                            status_text.error(f"Processing failed: {doc_status['error_message']}")
                            break
                        elif status == 'processing':
                            if doc_status['total_chunks']:
                                progress = (doc_status['processed_chunks'] or 0) / doc_status['total_chunks']
                            status_text.info(f"Processing document... ({int(progress * 100)}%)")
                        
                        progress_bar.progress(progress)
                        time.sleep(2)
    
    with tab2:
        st.header("Document List")
        
        # Add refresh button
        if st.button("🔄 Refresh"):
            st.rerun()
        
        # Fetch and display documents
        documents = get_document_list(st.session_state.api_session)
        
        if not documents:
            st.info("No documents found")
        else:
            for doc in documents:
                with st.expander(f"📄 {doc['filename']}", expanded=False):
                    col1, col2, col3 = st.columns([2,2,1])
                    
                    with col1:
                        st.markdown(f"""
                        **Status:** :{get_status_color(doc['status'])}`{doc['status']}`  
                        **Size:** {format_size(doc['file_size'])}  
                        **Type:** {doc['file_type']}
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **Created:** {format_date(doc['created_at'])}  
                        **Chunks:** {doc['total_chunks'] or 'N/A'}  
                        **Processed:** {doc['processed_chunks'] or 'N/A'}
                        """)
                    
                    with col3:
                        if doc['status'] != 'deleted':
                            if st.button("🗑️ Delete", key=f"del_{doc['id']}"):
                                if delete_document(st.session_state.api_session, doc['id']):
                                    st.success("Document deleted successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Failed to delete document")
                    
                    if doc['error_message']:
                        st.error(f"Error: {doc['error_message']}")

if __name__ == "__main__":
    main()
