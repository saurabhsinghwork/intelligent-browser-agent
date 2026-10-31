"""Launch the local Streamlit intelligent-browser application.

This entry point owns page configuration only. The UI delegates browser/provider
work to a spawn-safe worker process and never globally monkeypatches CreateProcess.
"""
# Handle Windows asyncio connection reset error on abrupt client disconnection.
import sys
# Apply connection-lost protection on Windows platforms only.
if sys.platform == "win32":
    # Import Windows proactor transport to catch socket reset exceptions.
    try:
        # Access the Windows event-loop transport used by the local server.
        from asyncio.proactor_events import _ProactorBasePipeTransport
        # Preserve the implementation supplied by the current Python runtime.
        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost
        # Retain the existing disconnect guard without altering its behavior.
        def _safe_call_connection_lost(self, exc):
            """Allow the existing server transport to close after a client socket reset."""
            # Delegate normal shutdown to the original transport implementation.
            try:
                # Preserve transport callbacks and resource release on an ordinary close.
                _orig_call_connection_lost(self, exc)
            # The existing application suppresses reset errors during disconnection.
            except (ConnectionResetError, OSError):
                # Keep this pre-existing compatibility behavior unchanged.
                pass
        # Install the existing platform-specific disconnect wrapper.
        _ProactorBasePipeTransport._call_connection_lost = _safe_call_connection_lost
    # Python implementations without this private transport need no wrapper.
    except (ImportError, AttributeError):
        # Continue with the runtime's standard disconnect handling.
        pass
# Configure the local application page before rendering widgets.
import streamlit as st
# Keep presentation and process ownership in their dedicated modules.
from ui.view import render_app

# Guard execution so spawned multiprocessing workers do not re-run Streamlit rendering.
if st.runtime.exists():
    # Set a readable local application title and working layout.
    st.set_page_config(page_title="Intelligent Browser Agent", layout="wide")
    # Draw the website-first configuration and responsive current-run controls.
    render_app()
