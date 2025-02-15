# app/frontend/utils.py
from datetime import datetime
import humanize

def format_size(size_bytes: int) -> str:
    """Format bytes into human readable size"""
    return humanize.naturalsize(size_bytes)

def format_date(iso_date_str: str) -> str:
    """Format ISO date string to readable format"""
    if not iso_date_str:
        return ""
    dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
    return dt.strftime('%Y-%m-%d %H:%M:%S')
