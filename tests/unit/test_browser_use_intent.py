"""Verify Browser Use distinguishes agent navigation from advertising page targets."""
# Control the monotonic clock without opening Chrome or making network requests.
from unittest.mock import patch
# Provide a minimal active Browser Use page identity without starting Chrome.
from types import SimpleNamespace
# Exercise the production Browser Use policy state directly.
from browser.browser_use import BrowserUseAdapter


# An active page redirect needs current agent intent before autonomous navigation.
def test_primary_page_external_destination_requires_current_intent():
    """Block an unsolicited external redirect on the selected actor page."""
    # Construct policy state without allocating a Browser Use runtime.
    adapter = BrowserUseAdapter()
    # Identify the one selected actor-page CDP session.
    adapter._primary_sessions = {"primary"}
    # No concrete click or direct navigation established current intent.
    assert adapter._should_request_hostname("primary") is False
    # An unsolicited active-page redirect must not reach the hostname handoff.
    assert adapter._record_denied_destination("primary", "https://external.example/path") is False


# A background advertisement target must never interrupt the user's task.
def test_unsolicited_ad_page_is_blocked_without_hostname_prompt():
    """Reject a child ad target without storing it as a requested destination."""
    # Construct policy state without starting Chrome.
    adapter = BrowserUseAdapter()
    # Simulate a child target long after any agent input interval.
    with patch("browser.browser_use.time.monotonic", return_value=20.0):
        # Register the attached advertising page through the real classification helper.
        adapter._register_attached_page("ad-session", "ad-target")
    # Apply the same denied-destination recording used by CDP interception.
    recorded = adapter._record_denied_destination("ad-session", "https://tracker.example/sync")
    # The target is denied without asking the user to approve an advertisement.
    assert recorded is False
    # No stale tracker URL may reach the Streamlit assistance panel.
    assert adapter._blocked_url == ""
    # Scoped cleanup retains only the exact child target identity.
    assert adapter._guarded_targets["ad-session"] == "ad-target"


# A popup created immediately by the agent's concrete click may navigate autonomously.
def test_current_click_popup_preserves_navigation_intent():
    """Bind popup autonomy to the short click interval and its concrete child session."""
    # Construct policy state without starting Chrome.
    adapter = BrowserUseAdapter()
    # Freeze monotonic time throughout classification so the bounded intent remains current.
    with patch("browser.browser_use.time.monotonic", return_value=100.0):
        # Mark the click interval through the production method.
        adapter._begin_navigation_intent()
        # Attach the popup while that click interval remains active.
        adapter._register_attached_page("popup-session", "popup-target")
        # The popup may continue only while it is causally attached to that agent input.
        assert adapter._should_request_hostname("popup-session") is True
    # Autonomous intended navigation does not populate a user-approval URL.
    assert adapter._blocked_url == ""


# A later child target must not inherit an earlier click's authority.
def test_expired_click_does_not_authorize_later_child_page():
    """Prevent stale input intent from converting later advertising pages into prompts."""
    # Construct policy state without starting Chrome.
    adapter = BrowserUseAdapter()
    # Start an intent interval at a known clock value.
    with patch("browser.browser_use.time.monotonic", return_value=5.0):
        # Record the concrete earlier click.
        adapter._begin_navigation_intent()
    # Attach another page after the bounded interval has expired.
    with patch("browser.browser_use.time.monotonic", return_value=8.0):
        # Register the later target through the production helper.
        adapter._register_attached_page("late-session", "late-target")
    # The later child cannot request hostname authorization from stale intent.
    assert adapter._should_request_hostname("late-session") is False


# An attached protocol session for the selected actor still needs current intent.
def test_active_actor_child_session_does_not_bypass_intent():
    """Identify the active tab by target ID without trusting delayed redirects."""
    # Construct policy state without opening a browser.
    adapter = BrowserUseAdapter()
    # Model the stable target identity exposed by the active Browser Use actor.
    adapter._page = SimpleNamespace(_target_id="active-target")
    # Register its attached protocol session after the click interval has expired.
    with patch("browser.browser_use.time.monotonic", return_value=50.0):
        # Use the production target classifier instead of modifying primary state directly.
        adapter._register_attached_page("active-child-session", "active-target")
    # Active-page identity alone cannot authorize a delayed script redirect.
    assert adapter._should_request_hostname("active-child-session") is False
    # The actor target must remain available for exact cleanup and tab ownership.
    assert adapter._guarded_targets["active-child-session"] == "active-target"
