"""Test real headless/headful session handoff with a synthetic human-only gate.

No actual CAPTCHA is solved and no credentials are used. A controlled native click
simulates the user, then profile reuse and restored headless state are verified.
"""
# Resolve project imports for the explicit diagnostic entry point.
import sys
from pathlib import Path
# Serve only local synthetic assistance content.
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
# Preserve working-directory state while configuring the fixture handler.
from functools import partial
# Run the owned local HTTP fixture concurrently.
from threading import Thread
# Bound readiness after the simulated human action.
import time
# Resolve actual runtime modules for direct execution.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Exercise the real selected method and the same handoff helper as production.
from services.run_controller import create_browser_adapter, _assist
# Supply the actual monitor/response contract.
from services.monitoring import RunMonitor
# Dispatch a native input in the controlled visible assistance session.
from domain.models import AgentDecision


# Simulate only the human response while keeping actual browsers and session transfer real.
class HumanMonitor(RunMonitor):
    """Complete a synthetic visible step, then explicitly respond Resume."""

    # Retain the owned real adapter for this controlled simulation.
    def __init__(self, adapter):
        """Initialize compatible monitoring with a reference to this test's browser."""
        # Keep source events and cancellation compatible with the production helper.
        super().__init__()
        # No unrelated browser or user profile is accessed.
        self.adapter = adapter

    # Replace only the human's manual interaction, not the transfer implementation.
    def await_response(self):
        """Click Continue in the actual visible browser and wait for proved authentication."""
        # The handoff must expose a real visible browser before asking the person to act.
        assert self.adapter.headful
        # Observe the actual synthetic assistance interface.
        observation = self.adapter.observe()
        # Resolve the current actual Continue button.
        target = next(item for item in observation.elements if item.get("dom_id") == "continue")
        # Dispatch trusted native input through the selected browser method.
        self.adapter.execute(AgentDecision(kind="click", target=target["id_label"], observation_id=observation.observation_id))
        # Wait for the actual page reload rather than immediately returning guessed success.
        deadline = time.monotonic() + 5
        # Re-observe through transient document replacement.
        while time.monotonic() < deadline:
            # The rendered protected text proves the synthetic step succeeded.
            if "Authenticated source" in self.adapter.probe()["text"]:
                # Resume is an explicit response, not elapsed-time authorization.
                return {"action": "resume"}
            # Keep the local readiness wait short.
            time.sleep(0.05)
        # A real failure must not be called completed assistance.
        raise AssertionError("Synthetic user assistance did not reach protected source")


# Verify the production transfer helper with one actual executor.
def main():
    """Preserve session cookies through headless -> visible assistance -> headless."""
    # Select the actual transport under test.
    method = sys.argv[1] if len(sys.argv) > 1 else "browser_use"
    # Bind an unused local fixture port.
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent / "fixtures")))
    # Serve the synthetic assistance interface concurrently.
    Thread(target=server.serve_forever, daemon=True).start()
    # Construct exactly one selected method.
    adapter = create_browser_adapter(method)
    # Simulate the human response only after a real visibility transition.
    monitor = HumanMonitor(adapter)
    # Keep the origin stable across profile reuse.
    site = f"http://127.0.0.1:{server.server_port}/login.html"
    # Release owned resources on both success and failure.
    try:
        # Begin in the user's selected background mode.
        adapter.initialize(site, False)
        # Preserve the actual starting observation in the logical task checkpoint.
        observation = adapter.observe()
        # The fixture must not be accidentally authenticated from another run.
        assert "User verification needed" in observation.text
        # Reuse the production cancellation event during transfer.
        adapter.stop_event = monitor.stop_event
        # Request a concrete human-only step without inventing a success flag.
        state = {"selected_site": site, "headful": False, "authorized_external_domains": [], "observation": observation.__dict__, "waiting": {"kind": "captcha" if "--captcha" in sys.argv else "login"}}
        # Execute the exact production visibility/profile transfer behavior.
        _assist(state, adapter, monitor)
        # The user's original headless preference must be restored.
        assert not adapter.headful and not state["headful"]
        # Actual profile cookies must preserve the completed assistance step.
        assert "Original protected information." in adapter.observe().text
        # Automatic execution can resume only after a fresh observation is required.
        assert not state["waiting"] and not state["observation_ready"]
        # Report actual practical evidence without claiming a real CAPTCHA was automated.
        print({"method": method, "synthetic_step": "captcha-handoff" if "--captcha" in sys.argv else "login-handoff", "session_preserved": True, "headless_restored": True})
    # Preserve only this diagnostic's own resources.
    finally:
        # Close the owned selected-method session normally.
        adapter.close_or_detach()
        # Stop the private fixture service.
        server.shutdown()
        # Release the listening socket.
        server.server_close()


# Direct execution is required; imports must not launch browsers under Windows spawn.
if __name__ == "__main__":
    # Run only this explicit diagnostic.
    main()
