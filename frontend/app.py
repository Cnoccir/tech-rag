import streamlit as st

# Import views from the new `views` directory
from frontend.views.login import show_login
from frontend.views.document_library import show_document_library
from frontend.views.admin_management import show_admin_management
from frontend.views.chat import show_chat

def main():
    st.set_page_config(page_title="Tech RAG", layout="wide")

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "api_base_url" not in st.session_state:
        # Adjust to your real FastAPI URL if different
        st.session_state.api_base_url = "http://localhost:8000/api/v1"

    # If not logged in, show only the login form
    if not st.session_state.authenticated:
        show_login()
        return

    # Now the user is authenticated, build a custom sidebar
    st.sidebar.title("Navigation")

    # Everyone sees Document Library
    nav_options = ["Document Library"]

    # Show “Chat” only if a document is selected
    if "selected_document_id" in st.session_state:
        nav_options.append("Chat")

    # If user is admin, show Admin Panel
    if st.session_state.is_admin:
        nav_options.append("Admin Panel")

    choice = st.sidebar.radio("Go to", nav_options)

    # Route to selected view
    if choice == "Document Library":
        show_document_library()
    elif choice == "Chat":
        show_chat()
    elif choice == "Admin Panel":
        show_admin_management()

if __name__ == "__main__":
    main()
