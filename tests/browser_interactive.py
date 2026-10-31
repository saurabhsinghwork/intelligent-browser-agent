"""Verify native shadow input and exact finite interactive extraction in a real browser."""
# Resolve imports for this explicit diagnostic entry point.
import sys
# Resolve controlled fixture and source paths.
from pathlib import Path
# Serve only this test's deterministic local fixture directory.
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
# Bind a fixture root without changing the process working directory.
from functools import partial
# Keep the fixture server responsive during real browser input.
from threading import Thread
# Make project imports available for direct execution.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Select the real browser executor.
from services.run_controller import create_browser_adapter
# Preserve exact source through the actual collector.
from services.extraction import collect_page
# Inspect durable source blocks after virtual UI replacement.
from services.evidence import EvidenceStore
# Send actual observation-bound native input.
from domain.models import AgentDecision


# Exercise one actual browser executor against tabs and finite buttons.
def main():
    """Assert exact content survives tabs, pagination, expansion, and load-more controls."""
    # Choose the actual configured transport.
    method = sys.argv[1] if len(sys.argv) > 1 else "browser_use"
    # Bind a private unused local port.
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "fixtures")))
    # Serve the fixture independently of blocking browser calls.
    Thread(target=server.serve_forever, daemon=True).start()
    # Construct exactly one selected executor.
    adapter = create_browser_adapter(method)
    # Always close owned test resources after success or failure.
    try:
        # Open the real local interface.
        adapter.initialize(f"http://127.0.0.1:{server.server_port}/interactive.html", "--headed" in sys.argv)
        # Observe the real open-shadow target before input.
        observation = adapter.observe()
        # Resolve only the currently observed actual target.
        target = next(item for item in observation.elements if item.get("dom_id") == "shadowButton")
        # Dispatch trusted native input through the selected executor.
        adapter.execute(AgentDecision(kind="click", target=target["id_label"], observation_id=observation.observation_id))
        # Verify actual source changed inside the open shadow root.
        assert "Shadow source clicked" in adapter._evaluate("() => document.getElementById('shadow').shadowRoot.getElementById('shadowResult').innerText")
        # Preserve all replacement states outside model context limits.
        store = EvidenceStore(adapter._screenshot_dir)
        # Traverse the full finite interactive scope.
        report = collect_page(adapter, "main", store)
        # Export before assertions so a failure is reproducible.
        artifacts = store.export()
        # Read exact source strings rather than any model response.
        texts = [block["text"] for block in store.blocks()]
        # Every tab/page record must survive UI replacement.
        missing = [f"{tab} page {page} record {index}" for tab in ("Alpha", "Beta") for page in range(1, 4) for index in range(8) if f"{tab} page {page} record {index}" not in texts]
        # Missing any source record fails completeness even if the browser ran.
        assert not missing, (missing, artifacts)
        # Opening relevant details must preserve exact punctuation and values.
        assert "Expanded exact source: ₹42 — unchanged." in texts, artifacts
        # The finite load-more list must be exhausted.
        assert all(f"More record {index}" in texts for index in range(4)), artifacts
        # Successful source capture alone cannot replace finite traversal evidence.
        assert report["complete"], report
        # Report only actual verified records and retained source artifacts.
        print({"method": method, "tab_page_records": 48, "load_more_records": 4, "shadow_native_click": True, "complete": True, "artifacts": artifacts})
        # Release the source database after inspection.
        store.close()
    # Keep fixture and browser cleanup local to this run.
    finally:
        # Close only this test's browser/profile runtime.
        adapter.close_or_detach()
        # Stop the private local service.
        server.shutdown()
        # Release the listening socket.
        server.server_close()


# Test imports must not launch browsers or Windows worker processes.
if __name__ == "__main__":
    # Run only when explicitly requested.
    main()
