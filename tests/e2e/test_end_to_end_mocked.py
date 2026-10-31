"""Deterministic orchestration test with exact source evidence, not a fake success flag.

The fake executor simulates actual visible state and capture measurements. Separate
browser diagnostics exercise real transports; this test isolates graph lifecycle,
source assembly, model finish handling, cleanup, and credential-safe monitoring.
"""
# Model finite UI state with provider-neutral records.
from domain.models import BrowserObservation, AgentDecision
# Validate the same configuration used by the real application.
from config.settings import RunConfiguration
# Collect actual graph lifecycle events.
from services.monitoring import RunMonitor
# Execute real checkpointed LangGraph cycles and evidence export.
from services.run_controller import execute_run


# Simulate a finite search-results-product interface.
class MockControlledAdapter:
    """Provide visible page states and exact capture data for the actual collector."""

    # Keep test artifacts isolated from genuine reusable browser profiles.
    def __init__(self, directory):
        """Initialize a deterministic page and owned screenshot directory."""
        # Start before any search interaction.
        self.step = 0
        # Retain a concrete browser destination.
        self.url = "https://shop.example"
        # Record actual cleanup rather than assuming it happened.
        self.closed = False
        # Use only the test-owned artifact directory.
        self._screenshot_dir = directory

    # Preserve the selected destination while accepting explicit grants.
    def set_site(self, site, headful, authorized_domains=None):
        """Store the selected simulated website without opening a real browser."""
        # Keep the starting destination consistent with configuration.
        self.url = site

    # Simulate the common initialization boundary.
    def initialize(self, site, headful, session_reference=None):
        """Initialize the controlled executor at the selected website."""
        # No external network or provider credentials are used.
        self.url = site

    # Expose the actual state the simulated UI is currently displaying.
    def observe(self):
        """Return exact UI text rather than a model-generated answer."""
        # Landing page requires search before product extraction.
        if self.step == 0:
            # Source wording is deliberately different from the final product.
            return BrowserObservation(self.url, "Store", "Welcome to store. Search items below.")
        # Search results need a further product-link click.
        if self.step == 1:
            # Preserve the actual intermediate URL and wording.
            return BrowserObservation(self.url + "/search", "Results", "Running Shoes $85")
        # Product details provide the exact expected final source.
        return BrowserObservation(self.url + "/product/shoes", "Product", "Running Shoes price: $85. In stock.")

    # Simulate actual input effects independently from provider rationale.
    def execute(self, decision):
        """Advance the controlled UI only when the corresponding input is executed."""
        # Clicking search or a product link advances one visible state.
        if decision.kind == "click":
            # The next observation proves the state actually changed.
            self.step += 1
        # Supply explicit action metadata for deterministic effect verification.
        return {"success": True, "action": decision.kind}

    # Provide the actual source contract expected by the shared collector.
    def probe(self, mode="observe", **arguments):
        """Return finite measured capture data for the currently displayed product."""
        # This controlled page fits one viewport.
        if mode in {"measure", "reset", "scroll"}:
            # Report measured finite-end evidence rather than a truthy string.
            return {"id": "window", "top": 0, "height": 600, "viewport": 800, "bottom": True}
        # Read the current exact source record.
        observation = self.observe()
        # Preserve semantic source and concrete finite coverage.
        return {"url": observation.url, "title": observation.title, "text": observation.text, "blocks": [{"key": "product", "kind": "p", "text": observation.text, "y": 0, "x": 0}], "links": [], "containers": [{"id": "window"}], "limitations": [], "loading": False}

    # Keep collection cancellable even with a simulated executor.
    def check_cancelled(self):
        """Raise when the actual injected run stop event is set."""
        # execute_run supplies the same cancellation event as real adapters.
        if self.stop_event.is_set():
            # Cancellation remains distinct from task completion.
            raise InterruptedError("Stopped by user")

    # Save an explicitly fake transport artifact for isolated orchestration tests.
    def _screenshot(self, path):
        """Write a test marker; real browser screenshot correctness is tested separately."""
        # Keep the marker in this test's owned artifact directory.
        path.write_bytes(b"isolated-test-screenshot")
        # Preserve the transport's path contract.
        return str(path)

    # Verify that run cleanup occurs even after finalization.
    def close_or_detach(self):
        """Record release of the fake executor."""
        # Mark the resource as actually closed.
        self.closed = True


# Make deterministic navigation choices without paraphrasing source output.
class MockStepwiseProvider:
    """Simulate model decisions while leaving source collection to the real service."""

    # The provider interface is identical to the two live multimodal transports.
    def decide(self, task, observation, history):
        """Choose the next grounded step from the controlled visible state."""
        # The independent objective audit must cite exact actual product source.
        if "COMPLETION AUDIT" in task:
            # This quotation is separately checked against the durable source store.
            return AgentDecision(kind="finish", expected="objective_met", value='["Running Shoes price: $85. In stock."]')
        # Product text is captured by the collector, never rewritten into an answer.
        if observation.title == "Product":
            # Empty output is valid for a source-backed finish proposal.
            return AgentDecision(kind="finish")
        # Open the actual product result.
        if observation.title == "Results":
            # A click must execute before the next state can appear.
            return AgentDecision(kind="click", target="product")
        # Submit search after the field was filled.
        if any(item.get("decision", {}).get("kind") == "fill" for item in history):
            # Advance to real simulated results.
            return AgentDecision(kind="click", target="search")
        # Begin with a search field input.
        return AgentDecision(kind="fill", target="query", value="shoes")


# Verify exact source output and actual graph lifecycle.
def test_end_to_end_mocked_run(tmp_path):
    """Complete the controlled journey and export exactly the original product text."""
    # Keep the same provider/method contract as a live run.
    configuration = RunConfiguration("gemini", "browser_use", False, "test-key-not-persisted")
    # Isolate artifacts from genuine browser data.
    adapter = MockControlledAdapter(tmp_path)
    # Record actual progress and safe events.
    monitor = RunMonitor()
    # Execute the real collector, evidence store, graph, and controller.
    result = execute_run("Find price of running shoes", "https://shop.example", configuration, adapter, MockStepwiseProvider(), monitor)
    # Nonempty prose is insufficient; complete source evidence must verify.
    assert result["verified"] is True, result.get("blocker", result.get("last_error"))
    # The exact UI wording must survive unchanged.
    assert result["output"] == "Running Shoes price: $85. In stock."
    # The resource must actually have been released.
    assert adapter.closed
    # Credentials must not enter graph checkpoints or logs.
    assert "test-key-not-persisted" not in (tmp_path / "checkpoint.json").read_text(encoding="utf-8")
    # Safe monitoring remains inspectable.
    assert all("test-key-not-persisted" not in event.message for event in monitor.logs)
