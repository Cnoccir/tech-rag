import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8000"

if "api_session" not in st.session_state:
    session = requests.Session()
    st.session_state.api_session = session

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

def show_main_interface():
    st.title("Knowledge Assistant")
    st.write("Welcome to your Knowledge Assistant! Use the navigation in the sidebar to manage documents and chat.")

def main():
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_interface()

if __name__ == "__main__":
    main()
