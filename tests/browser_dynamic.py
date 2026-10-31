"""Verify delayed loading and virtualized rows through actual browser transports.

This explicit diagnostic uses only local deterministic fixtures and no model keys.
It compares all expected logical records and preserves artifacts on failure.
"""
# Resolve project imports for direct execution.
import sys
from pathlib import Path
# Serve only the controlled fixture directory.
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
# Avoid changing the application's working directory.
from functools import partial
# Keep the local test server responsive during actual browser operations.
from threading import Thread
# Measure actual extraction time rather than guessing speed from code structure.
import time
# Make root imports explicit for this diagnostic entry point.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Select the actual executor without constructing any provider client.
from services.run_controller import create_browser_adapter
# Exercise the real measured collector and durable evidence service.
from services.extraction import collect_page
from services.evidence import EvidenceStore


# Run one actual adapter against the difficult finite dynamic interface.
def main():
    """Assert all delayed records and recycled logical rows survive exact collection."""
    # Default to Browser Use for a short local diagnostic.
    method = sys.argv[1] if len(sys.argv) > 1 else "browser_use"
    # Bind a private fixture server on an unused local port.
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "fixtures")))
    # Serve controlled content concurrently with browser calls.
    Thread(target=server.serve_forever, daemon=True).start()
    # Construct one real selected executor.
    adapter = create_browser_adapter(method)
    # Ensure every failure still closes only owned resources.
    try:
        # Navigate to the local dynamic fixture.
        adapter.initialize(f"http://127.0.0.1:{server.server_port}/dynamic.html", "--headed" in sys.argv)
        # Keep exact source records next to immutable images.
        store = EvidenceStore(adapter._screenshot_dir)
        # Measure collection independently from browser startup and model latency.
        started = time.monotonic()
        # Traverse lazy loading and the nested virtualized viewport.
        report = collect_page(adapter, "main", store)
        # Compare complete original source records rather than output length.
        blocks = store.blocks()
        # Retain all delayed paragraphs in source order.
        lazy = [block["text"] for block in blocks if block["kind"] == "p" and block["text"].startswith("Lazy ")]
        # Inspect actual table/cell relationships for every recycled logical row.
        rows = [block for block in blocks if block["kind"] == "table_row"]
        # Export before assertions so failures remain reproducible.
        artifacts = store.export()
        # All twenty-four delayed records must appear exactly once and unchanged.
        assert lazy == [f"Lazy {index}: unchanged source" for index in range(24)], (lazy, artifacts)
        # Recreated DOM nodes must not duplicate or lose logical row identities.
        assert [row["cells"][0]["text"] for row in rows] == [f"Virtual {index}" for index in range(80)], (len(rows), artifacts)
        # Repeated values are legitimate eighty separate records.
        assert all(row["cells"][1]["text"] == "Repeated value" for row in rows), artifacts
        # Completion requires concrete stable container ends.
        assert report["complete"], report["limitations"]
        # Report measured practical evidence for the validation status document.
        print({"method": method, "lazy_records": len(lazy), "virtual_rows": len(rows), "scrolls": report["scrolls"], "seconds": round(time.monotonic() - started, 2), "artifacts": artifacts})
        # Release the owned evidence connection after assertions.
        store.close()
    # Browser failures must not leak the local server or runtime.
    finally:
        # Preserve the selected method's eligible reusable profile normally.
        adapter.close_or_detach()
        # Stop the owned fixture server.
        server.shutdown()
        # Release the socket for independent subsequent diagnostics.
        server.server_close()


# Ordinary unit-test collection must not launch browsers.
if __name__ == "__main__":
    # Run only through this explicit diagnostic entry point.
    main()
