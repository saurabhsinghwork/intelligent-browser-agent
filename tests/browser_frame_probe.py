"""Inspect public W3Schools frame content without assuming about:blank is empty."""
# Resolve repository imports for direct diagnostics.
import sys
# Locate the local application.
from pathlib import Path
# Enable direct repository imports.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
# Construct the real selected browser executor.
from services.run_controller import create_browser_adapter
# Traverse lazy-loaded frame states through production code.
from services.extraction import collect_page
# Own one diagnostic browser.
adapter=create_browser_adapter("playwright_mcp")
# Ensure public-page inspection always closes its owned browser.
try:
    # Open the real operators page without a paid model call.
    adapter.initialize("https://www.w3schools.com/python/python_operators.asp",False)
    # Trigger the actual lazy-loaded bottom state before checking displayed frame content.
    collect_page(adapter,"main")
    # Report content presence and rendering only; never infer emptiness from the frame URL.
    print(adapter._evaluate("() => Array.from(document.querySelectorAll('#main iframe')).map(frame=>{const doc=frame.contentDocument;return {src:frame.src,title:frame.title,name:frame.name,accessible:!!doc,ready:doc?.readyState,text:doc?.body?.innerText,visual:doc?Array.from(doc.querySelectorAll('img,canvas,svg,video,input,button,iframe')).filter(el=>el.getBoundingClientRect().width&&el.getBoundingClientRect().height).map(el=>({tag:el.tagName,role:el.getAttribute('role'),label:el.getAttribute('aria-label'),hidden:el.getAttribute('aria-hidden'),text:el.textContent?.slice(0,300)})):null};})"))
# Release only the owned diagnostic Chrome process.
finally:
    # Keep the user's active CLI task unaffected.
    adapter.close_or_detach()
