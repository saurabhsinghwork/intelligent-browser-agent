"""Exercise real Streamlit widgets without starting a paid model request.

Discovery is injected only to isolate UI behavior. Real keyless search and browser
execution are tested separately through their actual runtime entry points.
"""
# Drive actual Streamlit widget and rerun semantics.
from streamlit.testing.v1 import AppTest
# Resolve the actual application entry point.
from pathlib import Path
# Build safe deterministic real-result-shaped suggestions.
from domain.models import WebsiteCandidate


# Find a button by its user-facing label.
def _button(app, label):
    """Return the unique rendered control rather than depending on layout indices."""
    # Button order can change when assistance controls appear.
    return next(button for button in app.button if button.label == label)


# Website selection must be explicit, and search must not run on every keystroke.
def test_website_first_ui_requires_search_and_selection(monkeypatch):
    """Preserve Search action, no preselection, key validation, and exclusive method choices."""
    # Capture discovery invocations independently from widget updates.
    calls = []

    # Supply deterministic search results without network or model credentials.
    def discover(query, **kwargs):
        """Record an explicit Search and return three safe candidate shapes."""
        # Typing alone must never call this function.
        calls.append(query)
        # Preserve the intended misspelling correction in the displayed choices.
        return [WebsiteCandidate("Flipkart", "www.flipkart.com", "https://www.flipkart.com"), WebsiteCandidate("Amazon", "www.amazon.in", "https://www.amazon.in"), WebsiteCandidate("Example", "example.com", "https://example.com")]
    # Replace only search transport, not UI control logic.
    monkeypatch.setattr("ui.view.search_websites", discover)
    # Run the actual app and widgets.
    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"), default_timeout=15).run()
    # Initial rendering must be free of application exceptions.
    assert not app.exception
    # Missing website/task/key keeps Start unavailable.
    assert _button(app, "Start task").disabled
    # Editing a query must not automatically spend search requests.
    next(field for field in app.text_input if field.label == "Website name or domain").set_value("flikart").run()
    # An explicit button action is required.
    assert calls == []
    # Execute the real Search button logic.
    _button(app, "Search").click().run()
    # Search was invoked exactly once with the user's spelling.
    assert calls == ["flikart"]
    # A result must never be chosen just because it ranked first.
    assert app.radio[0].value is None
    # Require the actual intended website selection.
    app.radio[0].set_value("https://www.flipkart.com").run()
    # Task text remains the user's original instruction.
    app.text_area(key="task_input").set_value("Get all requested product details").run()
    # Missing model key still prevents process creation.
    assert _button(app, "Start task").disabled
    # Use a nonsecret marker only to test input validation, not an API request.
    app.text_input(key="gemini_key").set_value("not-a-real-key").run()
    # Configuration is now ready; do not click Start and contact a model.
    assert not _button(app, "Start task").disabled
    # Switch method using the real mutually exclusive checkbox callback.
    app.checkbox(key="method_browser_use").check().run()
    # Exactly one executor remains selected.
    assert app.checkbox(key="method_browser_use").value
    # Both sibling methods are deselected.
    assert not app.checkbox(key="method_playwright_cli").value and not app.checkbox(key="method_playwright_mcp").value


# Provider names and enabled key fields must match the actual selected service.
def test_provider_exclusivity_and_active_key():
    """Select Groq without selecting Gemini or enabling its inactive key input."""
    # Run the actual application without discovery/network work.
    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py")).run()
    # Switch through the actual checkbox callback.
    app.checkbox(key="provider_groq").check().run()
    # Keep a single correct provider identifier.
    assert app.session_state["provider"] == "groq"
    # Exactly one provider checkbox remains selected.
    assert app.checkbox(key="provider_groq").value and not app.checkbox(key="provider_gemini").value
    # Only the selected provider's credential field is active.
    assert app.text_input(key="gemini_key").disabled and not app.text_input(key="groq_key").disabled
    # Configuration changes must not produce runtime errors.
    assert not app.exception

# Visibility is a persistent explicit choice rather than an unkeyed transient widget.
def test_browser_visibility_persists_across_configuration_reruns():
    """Keep both selected visibility modes through provider and method changes."""
    # Render actual Streamlit widget state without contacting a provider.
    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"), default_timeout=15).run()
    # Visible execution is the initial user-facing default.
    assert app.toggle(key="show_browser_window").value
    # Explicit headless selection must survive an unrelated configuration rerun.
    app.toggle(key="show_browser_window").set_value(False).run()
    # Switching an actual method must not silently reset visibility.
    app.checkbox(key="method_playwright_cli").check().run()
    # Keep background mode until the user explicitly changes it.
    assert not app.toggle(key="show_browser_window").value
    # Return to the requested visible mode through the real control.
    app.toggle(key="show_browser_window").set_value(True).run()
    # Provider selection also must not change the visible-browser requirement.
    app.checkbox(key="provider_groq").check().run()
    # The exact persisted user choice remains visible mode.
    assert app.toggle(key="show_browser_window").value and not app.exception
