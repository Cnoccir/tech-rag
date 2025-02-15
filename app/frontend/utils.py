import requests
import humanize
from datetime import datetime

def format_size(size_bytes: int) -> str:
    return humanize.naturalsize(size_bytes)

def format_date(iso_date_str: str) -> str:
    if not iso_date_str:
        return ""
    dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_documents(session: requests.Session, base_url: str, category_filter=None, include_deleted=False) -> list:
    """
    Calls GET /documents/list with optional category & include_deleted.
    """
    params = {}
    if category_filter:
        params["category"] = category_filter
    if include_deleted:
        params["include_deleted"] = True

    r = session.get(f"{base_url}/documents/list", params=params)
    r.raise_for_status()  # Raise HTTPError if bad status
    return r.json()

def search_documents(session: requests.Session, base_url: str, query: str, category_filter: str) -> list:
    """
    Calls GET /documents/search?query=...&category=...
    """
    params = {"query": query}
    if category_filter:
        params["category"] = category_filter

    r = session.get(f"{base_url}/documents/search", params=params)
    r.raise_for_status()
    return r.json()

def upload_document(session: requests.Session, base_url: str, file_obj, category: str) -> bool:
    """
    Calls POST /documents/upload, returns True if 2xx, else False.
    """
    files = {"file": (file_obj.name, file_obj, file_obj.type)}
    data = {"category": category}
    resp = session.post(f"{base_url}/documents/upload", files=files, data=data)
    return resp.status_code == 200
