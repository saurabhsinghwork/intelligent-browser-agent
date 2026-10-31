"""Verify complete per-entity collection through one selected real browser transport."""
# Resolve direct project imports.
import sys
# Convert browser observations into ordinary state dictionaries.
from dataclasses import asdict
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
# Exercise the production collection node and its detail-region selection.
from agent.nodes import _collect
# Compile and measure the same generalized full-detail goal used by production.
from agent.goals import compile_goal, measure_progress
# Execute clicks through the shared typed action contract.
from domain.models import AgentDecision
# Create exactly the requested actual browser executor.
from services.run_controller import create_browser_adapter
# Assemble task-relevant exact output through the durable evidence store.
from services.evidence import EvidenceStore


# Exercise one transport without provider credentials.
def main():
    """Collect ten expanded details without counting their compact selection controls."""
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
        # Navigate to the finite controlled master-detail interface.
        adapter.initialize(f"http://127.0.0.1:{server.server_port}/goal_details.html", False)
        # Compile an explicit finite full-detail task without any website-specific plan rule.
        task = "collect 10 Python jobs in Pune with complete details, not only job cards"
        # Retain the generated completion contract across all ten entity states.
        goal = compile_goal(task)
        # Store exact source outside browser and model prompt limits.
        store = EvidenceStore(adapter._screenshot_dir)
        # Keep production collection state between independently selected entities.
        state = {"adapter": adapter, "store": store, "task": task, "goal": goal, "visited": [], "collected_pages": {}, "screenshots": [], "progress": {}}
        # Open and collect every distinct requested record.
        for index in range(1, 11):
            # Bind the next click to a fresh immutable observation.
            observation = adapter.observe()
            # Resolve the actual current control by its website-owned DOM ID.
            target = next(item for item in observation.elements if item.get("dom_id") == "record-" + str(index))
            # Select this entity through the same native action path as the agent.
            adapter.execute(AgentDecision(kind="click", target=target["id_label"], observation_id=observation.observation_id))
            # Observe the resulting detail state before production region selection.
            state["observation"] = asdict(adapter.observe())
            # Reproduce a model selecting the listing main while the detail pane is its sibling.
            updates = _collect(state, "main")
            # Carry every durable progress and coverage update into the next selection.
            state.update(updates)
        # Read only complete detail aggregates selected by the explicit goal.
        selected = store.selected_blocks(goal)
        # Recompute the same finite completion predicate used by the graph.
        progress = measure_progress(goal, store.blocks())
        # Require exactly ten unique complete logical entities.
        assert len(selected) == 10 and progress["complete"], (len(selected), progress)
        # Every record must preserve the task constraints and expanded source.
        assert all("Python" in block["text"] and "Pune" in block["text"] and "Requirements" in block["text"] for block in selected), selected
        # Compact selection buttons alone must never be presented as complete results.
        assert all(block.get("detail_complete") is True and len(block["text"]) >= 200 for block in selected), selected
        # Report concise evidence for practical transport validation.
        print({"method": method, "complete_details": len(selected), "progress": progress, "cards_counted": False})
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
