# app/frontend/app.py
import streamlit as st
import sys
from pathlib import Path

# Add the project root to Python path
root_path = str(Path(__file__).parent.parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

# Use absolute imports
from app.frontend.pages.login import show_login
from app.frontend.pages.document_library import show_document_library
from app.frontend.pages.admin_management import show_admin_management
from app.frontend.pages.chat import show_chat

def main():
    """Main Streamlit application entry point"""
    st.set_page_config(page_title="Tech RAG", layout="wide")

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "api_base_url" not in st.session_state:
        st.session_state.api_base_url = "http://localhost:8000/api/v1"

    # Show login or main navigation
    if not st.session_state.authenticated:
        show_login()
        return

    # Navigation sidebar
    st.sidebar.title("Navigation")
    pages = ["Document Library", "Chat"]
    if st.session_state.is_admin:
        pages.append("Admin Panel")

    choice = st.sidebar.radio("Go to", pages)

    # Route to selected page
    if choice == "Document Library":
        show_document_library()
    elif choice == "Chat":
        show_chat()
    elif choice == "Admin Panel":
        show_admin_management()

if __name__ == "__main__":
    main()
