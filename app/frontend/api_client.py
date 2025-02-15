# app/frontend/api_client.py
import requests
import streamlit as st
from typing import Optional, Dict, Any

class APIClient:
    """Centralized API client for consistent API interactions"""

    @staticmethod
    def get_session() -> requests.Session:
        """Get or create an authenticated session"""
        if "api_session" not in st.session_state:
            st.session_state.api_session = requests.Session()
        token = st.session_state.get("access_token", "")
        st.session_state.api_session.headers.update({"Authorization": f"Bearer {token}"})
        return st.session_state.api_session

    @staticmethod
    def get_base_url() -> str:
        """Get API base URL from session state"""
        return st.session_state.get("api_base_url", "")

    @classmethod
    def get(cls, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to API endpoint"""
        session = cls.get_session()
        base_url = cls.get_base_url()
        response = session.get(f"{base_url}/{endpoint.lstrip('/')}", params=params)
        response.raise_for_status()
        return response.json()

    @classmethod
    def post(cls, endpoint: str, json: Optional[Dict] = None, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request to API endpoint"""
        session = cls.get_session()
        base_url = cls.get_base_url()
        response = session.post(
            f"{base_url}/{endpoint.lstrip('/')}",
            json=json,
            data=data,
            files=files
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def delete(cls, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request to API endpoint"""
        session = cls.get_session()
        base_url = cls.get_base_url()
        response = session.delete(f"{base_url}/{endpoint.lstrip('/')}")
        response.raise_for_status()
        return response.json()
