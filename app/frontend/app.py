import streamlit as st
from pages.login import show_login
from pages.document_library import show_document_library
from pages.admin_management import show_admin_management
from pages.chat import show_chat

def main():
    """
    Main Streamlit entry point.
    Manages user login state, sets up sidebar nav, calls page functions.
    """
    st.set_page_config(page_title="Tech RAG", layout="wide")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "api_base_url" not in st.session_state:
        # Adjust to your FastAPI server URL
        st.session_state.api_base_url = "http://localhost:8000/api/v1"

    # If not logged in, show login only
    if not st.session_state.authenticated:
        show_login()
        return

    # If logged in, show pages in sidebar
    st.sidebar.title("Navigation")
    pages = ["Document Library", "Chat"]
    if st.session_state.is_admin:
        pages.append("Admin Panel")

    choice = st.sidebar.radio("Go to", pages)

    if choice == "Document Library":
        show_document_library()
    elif choice == "Chat":
        show_chat()
    elif choice == "Admin Panel":
        show_admin_management()

if __name__ == "__main__":
    main()
