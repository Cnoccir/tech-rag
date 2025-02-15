import streamlit as st
import requests

def show_login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        api_base = st.session_state.get("api_base_url", "")
        try:
            resp = requests.post(
                f"{api_base}/auth/login",
                data={"username": username, "password": password},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                st.session_state["access_token"] = data["access_token"]
                st.session_state["token_type"] = data["token_type"]
                st.session_state["authenticated"] = True

                # fetch user info to see if admin
                st.session_state["is_admin"] = fetch_is_admin(api_base, data["access_token"])
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
        except Exception as e:
            st.error(f"Login request failed: {e}")


def fetch_is_admin(api_base_url: str, token: str) -> bool:
    """
    Example GET /auth/me => { "username": "..", "is_admin": boolean }
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{api_base_url}/auth/me", headers=headers, timeout=5)
        if r.status_code == 200:
            user_info = r.json()
            return bool(user_info.get("is_admin", False))
    except:
        pass
    return False
