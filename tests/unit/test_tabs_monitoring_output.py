"""Unit tests for tab selection, current-run monitoring, and result verification."""
# Import shared helpers and result formatter.
from browser.tab_manager import choose_active_tab
from services.monitoring import RunMonitor
from services.output import render_output
# Prefer a tab matching the current URL.
def test_tab_manager_prefers_current_url():
    # Arrange multiple tab records.
    tabs = [{"url":"https://a.example","active":False},{"url":"https://b.example","active":True}]
    # Assert the observed current URL takes priority.
    assert choose_active_tab(tabs, "https://a.example")["url"] == "https://a.example"
# Stop requests should be visible in monitoring state.
def test_stop_sets_event_and_status():
    # Arrange a new current-run monitor.
    monitor = RunMonitor()
    # Request cancellation.
    monitor.stop()
    # Assert the event and status update.
    assert monitor.snapshot()["stopped"] is True
    assert monitor.snapshot()["status"] == "Stop requested"
# Do not claim completion without verification.
def test_output_requires_verification():
    # Assert unverified results are not presented as completed output.
    assert "not been verified" in render_output("Looks done", verified=False)
# Redact secrets in monitoring logs.
def test_monitor_redacts_secrets_in_logs():
    # Arrange monitor and message with Gemini key and bearer token.
    monitor = RunMonitor()
    monitor.log("INFO", "Connecting with AIzaSyD1234567890123456789012345678901 and Bearer secret-token-value-12345")
    # Assert secrets are redacted from logs.
    last_log = monitor.snapshot()["logs"][-1].message
    assert "AIzaSy" not in last_log
    assert "secret-token-value" not in last_log
    assert "[REDACTED" in last_log
# Output renderer formats json list of dicts as markdown table.
def test_output_table_formatting():
    # Import format_output_presentation.
    from services.output import format_output_presentation
    # Arrange JSON list of records.
    json_data = '[{"product": "Laptop", "price": "$999"}, {"product": "Mouse", "price": "$29"}]'
    formatted = format_output_presentation(json_data)
    # Literal JSON displayed by a website remains literal JSON instead of an imposed table.
    assert formatted == json_data
