"""Exercise intercepted native wheels and real nested-panel traversal in installed Chrome."""
# Resolve repository imports for direct diagnostics.
import sys
# Locate the repository without depending on the launch directory.
from pathlib import Path
# Keep project modules available to this explicit diagnostic.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Construct only the selected genuine executor.
from services.run_controller import create_browser_adapter
# Exercise production finite-page collection rather than a simulated end condition.
from services.extraction import collect_page
# Preserve exact rendered source for inspection.
from services.evidence import EvidenceStore

# Keep browser creation explicit and cleanup unconditional.
def main():
    """Collect the whole real W3Schools UI including its independent navigation panel."""
    # Use the executor involved in the live failure by default.
    adapter = create_browser_adapter(sys.argv[1] if len(sys.argv)>1 else "playwright_mcp")
    # Store immutable source independently of model response limits.
    store = EvidenceStore(adapter._screenshot_dir)
    # Always release only this diagnostic's owned browser.
    try:
        # Show the actual installed Chrome browser and native pointer indicator.
        adapter.initialize("https://www.w3schools.com/python/python_operators.asp", True)
        # Force native wheel interception to verify the targeted recovery on this real page.
        adapter._evaluate("() => document.addEventListener('wheel',event=>event.preventDefault(),{passive:false})")
        # Deliberately retain full-body scope to include the formerly stuck navigation panel.
        report = collect_page(adapter, "body", store)
        # Require measured stable ends rather than merely successful input dispatch.
        assert report["containers"] and all(item["bottom"] and item["stable"] for item in report["containers"]), report
        # Verify that requested source survived the fallback traversal.
        assert "Python Operators" in store.text() and "Assignment" in store.text()
        # Export exact text, structure, and measured coverage for review.
        print({"complete":report["complete"],"scrolls":report["scrolls"],"containers":len(report["containers"]),"artifacts":store.export()})
    # Cleanup occurs even if coverage or source checks fail.
    finally:
        # Close the selected executor's actual Chrome window.
        adapter.close_or_detach()
        # Flush and close this diagnostic's evidence store.
        store.close()

# Importing this file must never launch a browser implicitly.
if __name__ == "__main__":
    # Run only when explicitly selected as a diagnostic.
    main()
