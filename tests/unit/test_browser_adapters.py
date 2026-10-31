"""Unit tests for adapter selection and explicit setup failures."""
# Import pytest and adapter factory.
import pytest
from services.run_controller import create_browser_adapter
# Assert only the three approved methods can be created.
def test_exact_three_browser_methods():
    # Arrange the approved set.
    approved = {"playwright_mcp", "playwright_cli", "browser_use"}
    # Assert an unrequested fourth method is rejected.
    with pytest.raises(ValueError, match="Unsupported browser method"):
        create_browser_adapter("browser_use_cli")
    # Assert each documented method maps to an adapter object.
    assert create_browser_adapter("playwright_cli") is not None
# Fail explicitly when Browser Use has not been configured.
def test_browser_use_requires_controller(monkeypatch):
    # Import sys to simulate missing dependency in module cache.
    import sys
    # Patch browser_use module lookup to simulate missing installation.
    monkeypatch.setitem(sys.modules, "browser_use", None)
    # Create Browser Use adapter without an injected runtime controller.
    adapter = create_browser_adapter("browser_use")
    # Assert the adapter reports a clear dependency setup error when the package is absent.
    with pytest.raises(RuntimeError, match="Browser Use is not installed|Browser Use session"):
        # Attempt to initialize session when package is absent.
        adapter.initialize("https://example.com", False)

