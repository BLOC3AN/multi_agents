"""
Main Streamlit application for Multi-Agent System GUI.
"""
import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from gui.pages.login import show_login_page
from gui.pages.chat import show_chat_page


def main():
    """Main application entry point."""
    
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # Route to appropriate page
    if st.session_state.authenticated:
        show_chat_page()
    else:
        show_login_page()


if __name__ == "__main__":
    main()
