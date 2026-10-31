"""Verify one generalized rendered-overlay dismissal through a selected real executor."""
# Resolve direct project imports.
import sys
# Serve the deterministic local fixture without external services.
from functools import partial
# Use a private threaded local HTTP service.
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
# Resolve project and fixture paths portably.
from pathlib import Path
# Keep fixture serving concurrent with blocking browser calls.
from threading import Thread
# Make the project root importable during direct diagnostics.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Compile the same goal record supplied by production orchestration.
from agent.goals import compile_goal
# Create exactly one user-selected real browser executor.
from services.run_controller import create_browser_adapter
# Traverse through the shared collector where delayed overlays can block scrolling.
from services.extraction import collect_page
# Store real source evidence separately from model output.
from services.evidence import EvidenceStore
# Reuse the production optional-interruption classifier for the final assertion.
from services.interruptions import find_dismissible_interruption


# Exercise the requested executor without model credentials.
def main():
    """Dismiss one optional sign-in modal and complete ordinary source collection."""
    # Default to Browser Use while accepting the other production method identifiers.
    method = sys.argv[1] if len(sys.argv) > 1 else "browser_use"
    # Bind an unused private port serving only controlled fixture files.
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "fixtures")))
    # Serve the page concurrently with real browser transport calls.
    Thread(target=server.serve_forever, daemon=True).start()
    # Instantiate only the selected production adapter.
    adapter = create_browser_adapter(method)
    # Preserve cleanup after every assertion or transport failure.
    try:
        # Open the controlled page using the adapter's normal guard and cursor setup.
        adapter.initialize(f"http://127.0.0.1:{server.server_port}/interruptions.html", False)
        # Keep collected evidence inside this isolated run artifact directory.
        store = EvidenceStore(adapter._screenshot_dir)
        # Run ordinary page collection with a non-login information objective.
        report = collect_page(adapter, "main", store, goal=compile_goal("retrieve all research result details from this page"))
        # Observe the actual post-collection interface.
        observation = adapter.observe()
        # The optional sign-in interruption must no longer expose a dismiss target.
        assert find_dismissible_interruption(observation.elements, "retrieve all research result details from this page") is None
        # Requested source remains exact and available after dismissal.
        assert "Generalized browser result content." in store.text()
        # Finite controlled content must still reach its ordinary traversal end.
        assert report["traversal_complete"], report
        # Report compact practical evidence without source or credentials.
        print({"method": method, "optional_overlay_dismissed": True, "traversal_complete": True})
        # Release this diagnostic's evidence database handle.
        store.close()
    # Close only resources created by this diagnostic.
    finally:
        # Release the selected owned browser runtime.
        adapter.close_or_detach()
        # Stop the private local fixture service.
        server.shutdown()
        # Release the bound socket for independent repeat tests.
        server.server_close()


# Avoid browser launch during ordinary test discovery.
if __name__ == "__main__":
    # Run only through an explicit practical diagnostic command.
    main()
