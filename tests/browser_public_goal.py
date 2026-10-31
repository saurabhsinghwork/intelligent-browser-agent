"""Run a finite information goal against a caller-supplied public page without model calls.

This diagnostic validates the shared browser, interruption, extraction, deduplication,
and completion layers while keeping website-specific URLs out of production logic.
"""
# Read an explicit method, URL, task, and optional visibility flag.
import sys
# Resolve project imports during direct execution.
from pathlib import Path
# Make the repository root importable without changing the working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Compile the same generalized finite goal used by LangGraph.
from agent.goals import compile_goal, measure_progress
# Create only the requested real browser implementation.
from services.run_controller import create_browser_adapter
# Use the shared measured collector rather than a website-specific scraper.
from services.extraction import collect_page
# Preserve exact rendered evidence and logical record identity.
from services.evidence import EvidenceStore


# Exercise one public interface through application-owned components only.
def main():
    """Collect and verify a caller-specified finite record goal."""
    # Require an explicit production method for reproducible diagnostics.
    method = sys.argv[1]
    # Keep the concrete acceptance URL outside reusable production code.
    url = sys.argv[2]
    # Preserve the user's natural-language objective verbatim.
    task = sys.argv[3]
    # Show the real browser only when the caller explicitly supplies `headed`.
    headful = len(sys.argv) > 4 and sys.argv[4].lower() == "headed"
    # Instantiate exactly one selected executor.
    adapter = create_browser_adapter(method)
    # Preserve cleanup after network, anti-bot, or assertion failures.
    try:
        # Open the supplied destination with ordinary policy, cursor, and session handling.
        adapter.initialize(url, headful)
        # Compile entity, count, and constraints without naming the website.
        goal = compile_goal(task)
        # Store all source evidence within this owned diagnostic run.
        store = EvidenceStore(adapter._screenshot_dir)
        # Collect from the generalized page-content region with body fallback.
        report = collect_page(adapter, "__iba_page_content__", store, goal=goal)
        # Measure the same deterministic predicate used for final task verification.
        progress = measure_progress(goal, store.blocks())
        # Read only the exact requested number of unique qualifying source records.
        selected = store.selected_blocks(goal)
        # Require complete finite-goal evidence rather than a model-generated claim.
        assert progress["complete"] and report["task_complete"], (progress, report)
        # Require output cardinality to match the explicit user count exactly.
        assert len(selected) == int(goal["required_count"]), len(selected)
        # Publish compact evidence without dumping page source or credentials.
        print({"method": method, "headful": headful, "unique_records": len(selected), "scrolls": report["scrolls"], "task_complete": report["task_complete"]})
        # Release the diagnostic evidence database explicitly.
        store.close()
    # Close only the runtime owned by this diagnostic.
    finally:
        # Preserve profile state while releasing browser processes and protocol clients.
        adapter.close_or_detach()


# Avoid launching a public browser during ordinary pytest discovery.
if __name__ == "__main__":
    # Run only through an explicit diagnostic command.
    main()
