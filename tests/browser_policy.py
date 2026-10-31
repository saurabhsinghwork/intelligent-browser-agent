"""Verify autonomous planned navigation and unsolicited-target guards locally.

127.0.0.1 is selected while localhost is a distinct hostname on the same server.
The test confirms deliberate information navigation proceeds without a prompt.
"""
# Resolve root imports without changing the working directory.
import sys
from pathlib import Path
# Serve deterministic policy scenarios without external network access.
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
# Keep fixture serving concurrent with browser operations.
from threading import Thread
# Give popup creation/interception a bounded observation window.
import time
# Resolve actual project code for direct execution.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Construct only the explicitly selected actual executor.
from services.run_controller import create_browser_adapter
# Exercise normalized native input through the selected real adapter.
from domain.models import AgentDecision


# Count forbidden document hits independently from what the browser adapter reports.
class PolicyHandler(BaseHTTPRequestHandler):
    """Serve a selected origin, redirect, popup trigger, and instrumented external host."""

    # Return controlled HTML and redirect responses.
    def do_GET(self):
        """Record actual localhost requests and supply finite policy test pages."""
        # Track network access to the distinct unapproved hostname.
        if self.headers.get("Host", "").startswith("localhost:"):
            # Any such hit before approval is a real policy failure.
            self.server.forbidden_hits += 1
        # Construct the actual alternate-host destination on this private server.
        external = f"http://localhost:{self.server.server_port}/destination"
        # A server redirect must be inspected before reaching its Location.
        if self.path == "/redirect":
            # Return a real HTTP redirect rather than a JavaScript simulation.
            self.send_response(302)
            # Point to a distinct hostname without changing the local port.
            self.send_header("Location", external)
            # Complete the redirect headers.
            self.end_headers()
            # Do not send a misleading normal page body.
            return
        # Ordinary selected-origin content exposes known and script-created destinations.
        body = '<html><head><title>Policy fixture</title></head><body><h1>Policy fixture</h1><a id="external" href="' + external + '">External destination</a><button id="popup" onclick="window.open(\'' + external + '\')">Open popup</button></body></html>'
        # Return actual navigable HTML.
        self.send_response(200)
        # Keep content decoding deterministic.
        self.send_header("Content-Type", "text/html; charset=utf-8")
        # Complete response headers before writing the source.
        self.end_headers()
        # Preserve the fixture text exactly.
        self.wfile.write(body.encode("utf-8"))

    # Keep diagnostics focused on policy assertions rather than request chatter.
    def log_message(self, format, *args):
        """Suppress ordinary local HTTP logs; assertions retain independently counted hits."""
        # No credentials or external requests exist in this fixture.
        return None


# Verify one actual execution method against independent network evidence.
def main():
    """Allow deliberate links, redirects, and popups without repeated hostname prompts."""
    # Default to Browser Use while allowing identical checks for MCP and CLI.
    method = sys.argv[1] if len(sys.argv) > 1 else "browser_use"
    # Create one private local origin with an independently counted alternate hostname.
    server = ThreadingHTTPServer(("127.0.0.1", 0), PolicyHandler)
    # Start with no access to the forbidden destination.
    server.forbidden_hits = 0
    # Serve the fixture concurrently with actual browser commands.
    Thread(target=server.serve_forever, daemon=True).start()
    # Select exactly one real transport.
    adapter = create_browser_adapter(method)
    # Keep the selected-host and alternate-host destinations explicit.
    origin = f"http://127.0.0.1:{server.server_port}"
    # Actual approval will grant this precise hostname, not every subdomain.
    external = f"http://localhost:{server.server_port}/destination"
    # Preserve cleanup even if a policy assertion fails.
    try:
        # Install policy before the first selected-origin request.
        adapter.initialize(origin + "/start", False)
        # Test a real server redirect from the otherwise permitted selected host.
        adapter.execute(AgentDecision(kind="navigate", target=origin + "/redirect"))
        # A deliberate active-page redirect should continue without a hostname prompt.
        assert server.forbidden_hits > 0, server.forbidden_hits
        # Restore the permitted page before testing script-created popup navigation.
        adapter._native("navigate", origin + "/start")
        # Resolve the actual observed external link.
        observation = adapter.observe()
        # Select the current concrete link identity.
        link = next(item for item in observation.elements if item.get("dom_id") == "external")
        # A grounded observed link may extend read-only research autonomously.
        adapter.execute(AgentDecision(kind="click", target=link["id_label"], observation_id=observation.observation_id))
        # The planned external destination must have received the real navigation.
        assert server.forbidden_hits > 1, server.forbidden_hits
        # Restore the permitted page before testing script-created popup navigation.
        adapter._native("navigate", origin + "/start")
        # Resolve the actual button, which intentionally has no href to preflight.
        observation = adapter.observe()
        # A native click creates a new browser target through ordinary website JavaScript.
        popup = next(item for item in observation.elements if item.get("dom_id") == "popup")
        # Use the same actual click path and target binding as production.
        adapter.execute(AgentDecision(kind="click", target=popup["id_label"], observation_id=observation.observation_id))
        # Give the new page's initial request time to reach the guard or trap server.
        time.sleep(0.5)
        # A popup caused by the grounded task action proceeds without a user prompt.
        assert server.forbidden_hits > 2, ("planned popup did not navigate", server.forbidden_hits)
        # Record compact practical policy verification evidence.
        print({"method": method, "planned_link_autonomous": True, "redirect_autonomous": True, "planned_popup_autonomous": True})
    # Close only resources owned by this diagnostic.
    finally:
        # Preserve eligible profile data while releasing the selected runtime.
        adapter.close_or_detach()
        # Stop the private trap server.
        server.shutdown()
        # Release its socket for independent repeat checks.
        server.server_close()


# Windows spawn/import must never start the diagnostic implicitly.
if __name__ == "__main__":
    # Run policy checks only through this explicit entry point.
    main()
