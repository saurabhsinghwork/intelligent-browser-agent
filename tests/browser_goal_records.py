"""Verify finite generalized record goals through one selected real browser transport."""
# Resolve direct project imports.
import sys
# Serve only deterministic controlled fixture files.
from functools import partial
# Use a private local threaded HTTP service.
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
# Resolve project and fixture directories.
from pathlib import Path
# Keep the local server concurrent with blocking browser calls.
from threading import Thread
# Make the project root importable when this diagnostic runs directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Compile the same generalized finite goal used by production.
from agent.goals import compile_goal, measure_progress
# Create exactly the requested actual browser executor.
from services.run_controller import create_browser_adapter
# Traverse rendered source through the shared measured collector.
from services.extraction import collect_page
# Assemble task-relevant exact output through the durable evidence store.
from services.evidence import EvidenceStore


# Exercise one transport without provider credentials.
def main():
    """Collect exactly ten qualifying records and exclude sticky/global duplicates."""
    # Default to Browser Use while accepting all three production identifiers.
    method = sys.argv[1] if len(sys.argv) > 1 else "browser_use"
    # Bind a private unused local port.
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "fixtures")))
    # Serve controlled source without blocking the selected adapter.
    Thread(target=server.serve_forever, daemon=True).start()
    # Construct one real browser method.
    adapter = create_browser_adapter(method)
    # Preserve cleanup after every assertion or transport failure.
    try:
        # Navigate to the finite controlled record interface.
        adapter.initialize(f"http://127.0.0.1:{server.server_port}/goal_records.html", False)
        # Compile a natural-language task without any website-specific plan code.
        goal = compile_goal("collect 10 jobs of python in pune")
        # Retain source in this adapter's isolated run directory.
        store = EvidenceStore(adapter._screenshot_dir)
        # Stop local traversal as soon as ten unique qualifying records exist.
        report = collect_page(adapter, "main", store, goal=goal)
        # Read the exact task-relevant record subset.
        selected = store.selected_blocks(goal)
        # Measure completion from logical records rather than screenshot count.
        progress = measure_progress(goal, store.blocks())
        # Require exactly the user-requested number of unique entities.
        assert len(selected) == 10 and progress["complete"], (len(selected), progress)
        # Every record must retain both original task constraints.
        assert all("Python" in block["text"] and "Pune" in block["text"] for block in selected), selected
        # Global sticky/signup chrome must not appear in task-scoped output.
        assert "Join now" not in store.text(goal) and "Jobs" not in store.text(goal)
        # The collector must stop at the finite goal rather than exhaust all 24 records.
        assert report["task_complete"] and not report["traversal_complete"], report
        # Report compact evidence for practical transport validation.
        print({"method": method, "unique_records": len(selected), "scrolls": report["scrolls"], "task_complete": report["task_complete"], "duplicate_chrome": False})
        # Release the test-owned database connection.
        store.close()
    # Close only resources created by this diagnostic.
    finally:
        # Release the selected browser runtime.
        adapter.close_or_detach()
        # Stop the private local server.
        server.shutdown()
        # Release its socket immediately.
        server.server_close()


# Avoid browser launch during ordinary pytest import.
if __name__ == "__main__":
    # Run only through explicit practical diagnostics.
    main()
