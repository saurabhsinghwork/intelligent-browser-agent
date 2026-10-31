"""Transport contract tests with explicit fakes, separate from real-browser acceptance.

Fake MCP responses match the actual structured inspection/native-code contracts.
They must not make a nonexistent screenshot or loosely shaped tool result look valid.
"""
# Save isolated fake screenshot markers in the actual requested test path.
from pathlib import Path
# Construct provider-neutral actions and observations.
from domain.models import AgentDecision, BrowserObservation
# Exercise actual adapter wrappers.
from browser.browser_use import BrowserUseAdapter
from browser.playwright_mcp import PlaywrightMCPAdapter
from browser.playwright_cli import PlaywrightCLIAdapter


# Provide deterministic Browser Use controller injection without a live event loop.
class FakeController:
    """Own only explicit fake transport state for isolated wrapper tests."""

    # Retain concrete calls for assertions.
    def __init__(self):
        """Initialize an empty transport history."""
        # Do not allocate browsers or threads in a fake controller.
        self.calls = []

    # Preserve initialization arguments.
    def initialize(self, **kwargs):
        """Record the configured site and visibility."""
        # Keep the actual call visible to contract assertions.
        self.calls.append(("initialize", kwargs))

    # Return a correctly normalized shared record.
    def observe(self):
        """Supply deterministic current page evidence."""
        # No provider/model is involved in transport observation.
        return BrowserObservation("https://example.com", "Example", "Page")

    # Record actual dispatch rather than inventing task completion.
    def execute(self, decision):
        """Return only operation success, never a verified task flag."""
        # Preserve the action/target/value contract.
        self.calls.append((decision.kind, decision.target, decision.value))
        # Task verification happens separately.
        return {"success": True}

    # Keep the tab contract explicit.
    def manage_tabs(self):
        """Return the fake transport's actual page inventory."""
        # A single controlled tab is sufficient for this wrapper test.
        return [{"url": "https://example.com", "title": "Example"}]

    # Verify delegated cleanup.
    def close_or_detach(self):
        """Record release of the injected transport."""
        # No real browser resources exist in this isolated case.
        self.calls.append(("close",))


# Emulate typed MCP tool results, including actual requested screenshot paths.
class FakeMCPClient:
    """Record tool names and return the exact inspection/native-input shapes."""

    # Retain field state so native fill must have an observable effect.
    def __init__(self):
        """Initialize calls and the fake input's current value."""
        # Keep every actual transport operation inspectable.
        self.calls = []
        # Native fill changes this source state.
        self.value = ""

    # Supply tool-specific responses rather than accepting every arbitrary shape.
    def call_tool(self, name, arguments):
        """Return typed inspection, native operation, screenshot, and tab results."""
        # Retain the exact selected transport calls.
        self.calls.append((name, arguments))
        # Save an isolated marker so the base's file-existence check remains meaningful.
        if name == "browser_take_screenshot":
            # Use only the caller's run-owned artifact filename.
            Path(arguments["filename"]).write_bytes(b"fake-contract-png")
            # Return the common screenshot transport shape.
            return {"path": arguments["filename"]}
        # Provide real structured page-inspection fields.
        if name == "browser_evaluate":
            # Resolve a concrete current element for common policy/fill verification.
            if '"mode": "resolve"' in arguments["function"]:
                # Actual value state proves the fake input operation was dispatched.
                return {"id": "e4", "tag": "INPUT", "type": "search", "text": "Search", "href": "", "value": self.value, "disabled": False}
            # Supply the complete shared observation contract.
            return {"url": "https://example.com", "title": "Example", "text": "Page text", "elements": [{"id_label": "e4", "type": "search"}], "links": [], "containers": [], "limitations": [], "viewport": {"width": 1280, "height": 800, "dpr": 1}}
        # Native actions remain inside the actual selected MCP method.
        if name == "browser_run_code":
            # Tab inventory is a list, not an invented success mapping.
            if '"kind": "tabs"' in arguments["code"]:
                # Preserve actual tab metadata.
                return [{"id": "0", "url": "https://example.com", "active": True}]
            # Simulate a concrete input value change only on fill.
            if '"kind": "fill"' in arguments["code"]:
                # The test supplies this explicit value.
                self.value = "hello"
            # Other native operations report transport success only.
            return {"success": True}
        # Opening the empty initial tab is supported by the common MCP contract.
        return {"success": True}


# Verify controller injection does not allocate a live Browser Use session.
def test_browser_use_adapter_contract_with_controller():
    """Preserve shared observation/action/tab/cleanup behavior for injected transports."""
    # Supply an explicit deterministic fake.
    controller = FakeController()
    # Create the wrapper without a model or live event loop.
    adapter = BrowserUseAdapter(controller=controller)
    # Configure its actual navigation boundary.
    adapter.initialize("https://example.com", False)
    # Shared records survive transport normalization.
    assert adapter.observe().url == "https://example.com"
    # Concrete action dispatch preserves normalized input.
    assert adapter.execute(AgentDecision(kind="click", target="e1"))["success"]
    # Retain actual fake tab metadata.
    assert adapter.manage_tabs()[0]["url"] == "https://example.com"
    # Release the injected runtime explicitly.
    adapter.close_or_detach()


# Verify exact inspection and native-input contracts through the MCP transport.
def test_mcp_adapter_uses_official_tool_contract(tmp_path):
    """Native fill and screenshots go through MCP and prove an actual field-value change."""
    # Inject a typed transport rather than launching Node.
    client = FakeMCPClient()
    # Keep artifacts isolated in the test directory.
    adapter = PlaywrightMCPAdapter(client=client)
    # Replace only this test's run-owned artifact root.
    adapter._screenshot_dir = tmp_path
    # Install guards and navigate using the selected transport contract.
    adapter.initialize("https://example.com", True)
    # Capture actual typed fake observation plus saved image marker.
    observation = adapter.observe()
    # Bind the input action to the current observation.
    result = adapter.execute(AgentDecision(kind="fill", target="e4", value="hello", observation_id=observation.observation_id))
    # Verify source text and measured field state independently.
    assert observation.text == "Page text"
    # The common fill check must observe the new real fake value.
    assert result["success"] and client.value == "hello"
    # No direct alternative automation runtime may execute the operation.
    assert any(name == "browser_run_code" and '"kind": "fill"' in arguments["code"] for name, arguments in client.calls)


# Retain metadata normalization compatibility for readable CLI integrations.
def test_cli_snapshot_metadata_parser():
    """Read known metadata labels without modifying source page text."""
    # Supply the official readable header shape.
    text = "### Page\n- Page URL: https://example.com\n- Page Title: Example"
    # Preserve exact destination metadata.
    assert PlaywrightCLIAdapter._extract_label(text, "Page URL:") == "https://example.com"
    # Preserve the readable title.
    assert PlaywrightCLIAdapter._extract_label(text, "Page Title:") == "Example"
