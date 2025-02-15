import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv
import requests
import time
from typing import Optional
import humanize
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8000/api/v1"

if "api_session" not in st.session_state:
    session = requests.Session()
    st.session_state.api_session = session

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user against the FastAPI backend."""
    try:
        response = st.session_state.api_session.post(
            f"{st.session_state.api_base_url}/auth/login",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            st.session_state.api_session.headers.update({"Authorization": f"Bearer {token}"})
            return True
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
    return False

def show_login_page():
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state.authenticated = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def get_document_list(session: requests.Session) -> list:
    """Fetch list of documents from the API."""
    response = session.get(f"{st.session_state.api_base_url}/documents/list")
    if response.status_code == 200:
        return response.json()
    return []

def upload_document(session: requests.Session, file, category: str) -> Optional[dict]:
    """Upload a document to the API."""
    files = {'file': file}
    data = {'category': category}
    response = session.post(f"{st.session_state.api_base_url}/documents/upload", files=files, data=data)
    if response.status_code == 200:
        return response.json()
    st.error(f"Upload failed: {response.text}")
    return None

def delete_document(session: requests.Session, doc_id: str) -> bool:
    """Delete a document."""
    response = session.delete(f"{st.session_state.api_base_url}/documents/{doc_id}")
    return response.status_code == 200

def format_size(size_bytes: int) -> str:
    return humanize.naturalsize(size_bytes)

def format_date(date_str: str) -> str:
    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return date.strftime('%Y-%m-%d %H:%M:%S')

def show_document_management():
    st.title("Document Management")
    
    # Upload section
    st.subheader("Upload Document")
    uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "doc", "docx"])
    
    if uploaded_file is not None:
        # Category selection
        category = st.selectbox(
            "Select Category",
            ["GENERAL", "HONEYWELL", "TRIDIUM", "JOHNSON_CONTROLS"]
        )
        
        if st.button("Upload"):
            with st.spinner("Uploading..."):
                if upload_document(st.session_state.api_session, uploaded_file, category):
                    st.success("Document uploaded successfully!")
                    st.rerun()

    # Document list section
    st.subheader("Document Library")
    documents = get_document_list(st.session_state.api_session)
    
    if not documents:
        st.info("No documents found. Upload some documents to get started!")
        return

    for doc in documents:
        with st.expander(f"{doc['filename']} ({format_size(doc['file_size'])})"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"Status: {doc['status']}")
                st.write(f"Type: {doc['file_type']}")
                st.write(f"Category: {doc['category']}")
            with col2:
                if doc.get('title'):
                    st.write(f"Title: {doc['title']}")
                if doc.get('description'):
                    st.write(f"Description: {doc['description']}")
                if doc.get('tags'):
                    st.write(f"Tags: {doc['tags']}")
            with col3:
                if st.button("Delete", key=f"del_{doc['id']}"):
                    if delete_document(st.session_state.api_session, doc['id']):
                        st.success("Document deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete document")

def show_chat_interface():
    st.title("Chat")
    st.write("Chat interface coming soon!")

def show_main_interface():
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        selected_page = st.radio(
            "Go to",
            ["Document Management", "Chat"],
            key="navigation"
        )
        st.session_state.current_page = selected_page

    # Main content
    if st.session_state.current_page == "Document Management":
        show_document_management()
    elif st.session_state.current_page == "Chat":
        show_chat_interface()

def main():
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_interface()

if __name__ == "__main__":
    main()
