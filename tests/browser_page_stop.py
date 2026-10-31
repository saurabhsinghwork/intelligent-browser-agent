"""Verify the reported single-page stopping issue through an actual browser executor."""
# Resolve direct diagnostic imports and method arguments.
import sys
# Keep project imports independent of the launch directory.
from pathlib import Path
# Convert only typed browser records to graph state data.
from dataclasses import asdict
# Measure actual traversal without requesting a model key.
import time
# Resolve the application root for direct execution.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Exercise actual shared graph node behavior.
from agent.nodes import act_node, verify_node
# Launch exactly the selected real browser method.
from services.run_controller import create_browser_adapter
# Preserve exact source evidence during the practical test.
from services.evidence import EvidenceStore
# Supply actual progress and cancellation boundaries.
from services.monitoring import RunMonitor
# Request the same broad body capture that caused the reported issue.
from domain.models import AgentDecision


# Reproduce the user's W3Schools page-scoped task without a paid model request.
def main():
    """Stop after page content, without traversing the tutorial sidebar or link frontier."""
    # Default to the exact executor reported in the user's latest log.
    method = sys.argv[1] if len(sys.argv) > 1 else "playwright_cli"
    # Use the actual page from that supplied run.
    url = "https://www.w3schools.com/python/python_operators.asp"
    # Construct one genuine browser adapter.
    adapter = create_browser_adapter(method)
    # Capture source outside model-context limits.
    store = EvidenceStore(adapter._screenshot_dir)
    # Retain real measured collection status.
    monitor = RunMonitor()
    # Always close owned diagnostic resources.
    try:
        # Visibility is not under test here; preserve the already-fixed launch behavior.
        adapter.initialize(url, "--headed" in sys.argv)
        # Resolve the semantic main request even when the site uses a div with id=main instead of a main tag.
        semantic = adapter.probe("capture", scope="main")
        # Unrelated navigation panels must remain outside this semantic content region.
        assert len(semantic["containers"]) == 1
        # Stream actual capture progress through the same production monitor.
        adapter.monitor = monitor
        # Bind the real current observation before collection.
        observation = adapter.observe()
        # Reproduce the exact page-scoped instruction from the user checkpoint.
        state = {"task":"all python operators detail from that page", "adapter":adapter, "monitor":monitor, "store":store, "observation":asdict(observation), "decision":asdict(AgentDecision(kind="collect", target="body")), "visited":[], "collected_pages":{}, "discovered_links":[], "frontier":[], "screenshots":[]}
        # Measure the page traversal independently of startup and provider latency.
        started = time.monotonic()
        # Run actual scoped collection through the production action node.
        result = act_node(state)
        # A completed finite capture must propose finalization in this same graph cycle.
        assert result.get("candidate_finish"), result.get("last_error")
        # No unrelated chapter/link review may extend this page-only task.
        assert not result["discovered_links"] and not result["frontier"]
        # Inspect real measured stopping evidence.
        report = result["collected_pages"][url]
        # The unrelated tutorial sidebar must not be traversed.
        assert len(report["containers"]) == 1, report
        # The requested actual operators source must remain captured.
        assert "Python Operators" in store.text() and "Assignment" in store.text(), store.export()
        # Inline syntax highlighting must not split an actual one-line code example into separate records.
        assert any(block["kind"] == "code" and "print(10 + 5)" in block["text"] for block in store.blocks()), store.export()
        # Keep this diagnostic provider-free while exercising terminal coverage verification.
        terminal = verify_node({**state, **result, "task":""})
        # Incomplete embedded source is reported honestly but cannot restart browsing.
        assert terminal.get("finished"), terminal
        # Preserve inspectable evidence before diagnostic cleanup.
        artifacts = store.export()
        # Report actual page boundary and terminal-state proof.
        print({"method":method,"seconds":round(time.monotonic()-started,2),"scrolls":report["scrolls"],"containers":len(report["containers"]),"no_link_review":True,"finished":True,"artifacts":artifacts})
    # Preserve only this test's owned resources.
    finally:
        # Release the actual selected browser normally.
        adapter.close_or_detach()
        # Close the diagnostic's evidence database.
        store.close()


# Imports must not launch a real browser implicitly.
if __name__ == "__main__":
    # Run only this explicitly requested practical regression.
    main()
