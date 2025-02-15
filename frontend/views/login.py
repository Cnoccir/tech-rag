import streamlit as st
from frontend.api_client import APIClient

def show_login():
    """Login page view with proper form handling"""
    st.title("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password", key="password_input")

        submit = st.form_submit_button("Login")
        if submit:
            try:
                # Make login request
                response = APIClient.post(
                    "auth/login",
                    data={"username": username, "password": password}
                )
                # Store token in session
                st.session_state["access_token"] = response["access_token"]
                st.session_state["token_type"] = response["token_type"]
                st.session_state["authenticated"] = True

                # Retrieve user info
                user_info = APIClient.get("auth/me")
                st.session_state["is_admin"] = bool(user_info.get("is_admin", False))

                st.success("Login successful!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
