"""Run real credential-free adapter diagnostics against a controlled local page.

This is an explicit browser test entry point, not a mock. It starts a local HTTP
fixture, uses the selected actual transport, and writes owned screenshot evidence.
"""
# Resolve project imports when this file is run directly.
import sys
# Serve only the controlled fixture directory.
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
# Bind the handler directory without changing global working-directory state.
from functools import partial
# Run the local fixture server concurrently with the browser.
from threading import Thread
# Resolve fixture and project directories explicitly.
from pathlib import Path
# Add the project root for direct diagnostic execution.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Import actual adapters without initializing provider APIs.
from browser.playwright_cli import PlaywrightCLIAdapter
from browser.playwright_mcp import PlaywrightMCPAdapter
from browser.browser_use import BrowserUseAdapter
# Construct a grounded native-input decision.
from domain.models import AgentDecision
# Verify complete source capture through the actual selected browser method.
from services.extraction import collect_page
# Retain exact source and coverage artifacts for inspection.
from services.evidence import EvidenceStore


# Exercise one actual browser transport while keeping fixture lifecycle bounded.
def main():
    """Verify navigation, immutable screenshot, native fill/click, and typed scrolling."""
    # Select the requested actual adapter, defaulting to CLI for a short diagnostic.
    method = sys.argv[1] if len(sys.argv) > 1 else "cli"
    # Bind an unused local port and serve only public controlled test data.
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "fixtures")))
    # Start the owned local server without blocking browser execution.
    Thread(target=server.serve_forever, daemon=True).start()
    # Build one real selected transport rather than a fake controller.
    adapter = {"cli": PlaywrightCLIAdapter, "mcp": PlaywrightMCPAdapter, "browser_use": BrowserUseAdapter}[method]()
    # Preserve cleanup even when a browser operation fails.
    try:
        # Navigate to a controlled page with no external credentials or services.
        url = f"http://127.0.0.1:{server.server_port}/controlled.html"
        # Initialize the real selected executor at that exact controlled URL.
        adapter.initialize(url, "--headed" in sys.argv)
        # Visible startup must install the arrow before the slower first observation.
        if adapter.headful:
            # Inspect the document-start cursor without invoking observation-time recovery.
            startup_cursor = adapter._evaluate("() => {const cursor=document.getElementById('iba-cursor');const box=cursor?.getBoundingClientRect();return {version:cursor?.dataset.version,x:box?.left,y:box?.top};}")
            # The current arrow must already be visible at a real nonnegative browser coordinate.
            assert startup_cursor["version"] == "red-arrow-v3" and startup_cursor["x"] >= 0 and startup_cursor["y"] >= 0, startup_cursor
            # Inspect the controlled same-host frame to prevent duplicate cursor regressions.
            framed_cursor = adapter._evaluate("() => !!document.getElementById('cursor-frame').contentDocument?.getElementById('iba-cursor')")
            # Only the top-level browser document may display the application pointer.
            assert framed_cursor is False, framed_cursor
        # Inspect real browser text and capture an actual viewport screenshot.
        observation = adapter.observe()
        # The fixture must actually be loaded before testing its controls.
        assert observation.title == "Controlled Browser Task", observation.title
        # Locate the stable target through its observed search label.
        search = next(item for item in observation.elements if item["type"] == "search")
        # Fill using the exact observed identity and its originating observation.
        outcome = adapter.execute(AgentDecision(kind="fill", target=search["id_label"], value="native input", observation_id=observation.observation_id))
        # A successful transport is insufficient unless the real field retained its value.
        assert outcome["success"], outcome
        # Refresh the originating observation after the field value changed.
        observation = adapter.observe()
        # Resolve the correct duplicate label using its actual observed context/identity.
        correct = next(item for item in observation.elements if item.get("dom_id") == "correct")
        # Click the intended real element with a fresh bound reference.
        adapter.execute(AgentDecision(kind="click", target=correct["id_label"], observation_id=observation.observation_id))
        # A cursor animation is insufficient; verify the actual fixture action target.
        assert "Correct action" in adapter.probe()["text"] and "WRONG" not in adapter.probe()["text"]
        # Visible mode must show the pointer at the same actual input target.
        if adapter.headful:
            # Compare CSS viewport geometry without moving an independent visual cursor.
            pointer = adapter._evaluate("() => {const c=document.getElementById('iba-cursor').getBoundingClientRect();const t=document.getElementById('correct').getBoundingClientRect();return {x:c.left,y:c.top,left:t.left,right:t.right,top:t.top,bottom:t.bottom};}")
            # A decoy animation or guessed viewport center would fail this check.
            assert pointer["left"] <= pointer["x"] <= pointer["right"] and pointer["top"] <= pointer["y"] <= pointer["bottom"], pointer
        # Verify typed scroll metrics rather than string truthiness.
        metrics = adapter.probe("scroll", target="window", direction="down")
        # This long fixture must have advanced the actual window.
        assert metrics["top"] > 0, metrics
        # Report only safe runtime evidence and its immutable artifact reference.
        print({"method": method, "native_fill": True, "scroll_top": metrics["top"], "screenshot": observation.screenshot_path})
        # Complete traversal is an explicit longer diagnostic rather than ordinary test collection.
        if "--collect" in sys.argv:
            # Keep the evidence store local to this adapter's unique run.
            store = EvidenceStore(adapter._screenshot_dir)
            # Traverse actual long and nested regions without a model or fixed scroll cap.
            report = collect_page(adapter, "main", store)
            # Read the complete source records rather than a summarized answer.
            blocks = store.blocks()
            # Every original paragraph must appear exactly once despite viewport overlap.
            records = [block for block in blocks if block["text"].startswith("Record ")]
            # Nested-table rows must remain complete and associated with their cells.
            rows = [block for block in blocks if block["kind"] == "table_row" and block["cells"][0]["text"].startswith("Item ")]
            # Preserve enough evidence to debug every failed assertion.
            artifacts = store.export()
            # Compare exact record membership, not merely a plausible text length.
            assert [block["text"] for block in records] == [f"Record {index}: original wording" for index in range(60)], (len(records), artifacts)
            # Preserve repeated equal values as sixty legitimate separate rows.
            assert len(rows) == 60, (len(rows), artifacts)
            # Code indentation and blank lines must survive the actual rendered capture.
            assert any(block["kind"] == "code" and block["text"] == 'if ready:\n    print("exact")\n\n    return True' for block in blocks), artifacts
            # Honest completion requires measured stable ends, not a screenshot count.
            assert report["complete"], report["limitations"]
            # Retain measured practical verification evidence.
            print({"method": method, "complete": True, "records": len(records), "table_rows": len(rows), "scrolls": report["scrolls"], "artifacts": artifacts})
            # Release the owned database connection after exporting the evidence.
            store.close()
        # A full document replacement must recreate the cursor before another observation runs.
        if adapter.headful:
            # Navigate through the selected executor to the same safe fixture with a new document URL.
            adapter._native("navigate", url + "?cursor-document=2")
            # Read the init-script result immediately, without invoking the recovery path in observe().
            replaced_cursor = adapter._evaluate("() => {const cursor=document.getElementById('iba-cursor');const box=cursor?.getBoundingClientRect();return {version:cursor?.dataset.version,x:box?.left,y:box?.top};}")
            # Document-start installation and native movement must keep the cursor visible after navigation.
            assert replaced_cursor["version"] == "red-arrow-v3" and replaced_cursor["x"] >= 0 and replaced_cursor["y"] >= 0, replaced_cursor
    # Close only the owned browser/session and local server.
    finally:
        # Persist eligible session data while releasing the selected runtime.
        adapter.close_or_detach()
        # Stop the owned fixture server after browser cleanup.
        server.shutdown()
        # Release the socket promptly for repeated independent diagnostics.
        server.server_close()


# Avoid launching browsers when imported by ordinary unit-test collection.
if __name__ == "__main__":
    # Run diagnostics only through this explicit entry point.
    main()
