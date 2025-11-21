"""
Session state management for Streamlit application.
"""

import streamlit as st
from typing import Any


class SessionManager:
    """Manage Streamlit session state."""
    
    def set(self, key: str, value: Any) -> None:
        """Set a session state value."""
        st.session_state[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a session state value."""
        return st.session_state.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if key exists in session state."""
        return key in st.session_state
    
    def delete(self, key: str) -> None:
        """Delete a key from session state."""
        if key in st.session_state:
            del st.session_state[key]
    
    def clear_all(self) -> None:
        """Clear all session state."""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    def clear_pattern(self, pattern: str) -> None:
        """Clear keys matching a pattern."""
        keys_to_delete = [key for key in st.session_state.keys() if pattern in key]
        for key in keys_to_delete:
            del st.session_state[key]
    
    def get_all_keys(self) -> list:
        """Get list of all session state keys."""
        return list(st.session_state.keys())
