
import re

def display_label(s: str) -> str:
    """Used for UI display"""
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.lower()
    return s[:1].upper() + s[1:] if s else s

