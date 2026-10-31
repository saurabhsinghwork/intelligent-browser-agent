"""Verify generalized optional-overlay classification without launching a browser."""
# Exercise only the shared site-independent interruption policy.
from services.interruptions import find_dismissible_interruption


# Build one ordinary observed control record with explicit overrides.
def _control(**updates):
    """Return a minimal enabled, visible, overlay-bound close control."""
    # Supply the same fields emitted by the rendered page probe.
    value = {"id_label": "close-1", "text": "Dismiss", "aria_label": "Dismiss", "title": "", "overlay": True, "overlay_context": "Sign in to continue", "in_view": True, "disabled": False}
    # Let each test vary only the behavior it needs to establish.
    value.update(updates)
    # Return one JSON-safe observed element.
    return value


# Optional authentication interruptions should not stop information gathering.
def test_optional_sign_in_overlay_is_dismissed():
    """Select a grounded close control for a nonessential sign-in overlay."""
    # Classify one generic modal without a website-specific selector.
    selected = find_dismissible_interruption([_control()], "collect ten matching records")
    # Preserve the exact observed identity for native input.
    assert selected["id_label"] == "close-1"


# Icon-only close controls use their accessibility label when rendered text is absent.
def test_accessible_icon_close_is_dismissed():
    """Recognize an icon button through semantics and surrounding overlay purpose."""
    # Model a common cross-site close icon with no textual child node.
    selected = find_dismissible_interruption([_control(text="", aria_label="Close dialog", overlay_context="Create an account to keep reading")], "read this page")
    # The accessible close control is sufficiently grounded.
    assert selected is not None


# Accessibility labels may describe both the purpose and container being closed.
def test_descriptive_sign_in_close_label_is_dismissed():
    """Recognize a descriptive close label without requiring a site-specific phrase."""
    # Model an icon whose accessible name contains the optional interruption purpose.
    selected = find_dismissible_interruption([_control(text="", aria_label="Close sign-in dialog")], "read public results")
    # Overlay semantics and surrounding wording keep the broader label safe.
    assert selected is not None


# Ordinary close buttons outside overlays must remain available to task reasoning.
def test_page_close_control_is_not_treated_as_interruption():
    """Reject a close-like label that does not belong to an overlay."""
    # A normal page control has no popup ancestry.
    selected = find_dismissible_interruption([_control(overlay=False)], "collect records")
    # The policy must not click it automatically.
    assert selected is None


# Authentication requested by the task requires human assistance rather than dismissal.
def test_required_login_overlay_is_preserved():
    """Keep a sign-in modal when authentication is explicitly part of the task."""
    # State an explicit authentication objective.
    selected = find_dismissible_interruption([_control()], "sign me in to my account")
    # The login interface remains visible for the existing assistance handoff.
    assert selected is None


# Task dialogs such as filter panels are not optional promotional interruptions.
def test_unrelated_task_dialog_is_preserved():
    """Require a known optional-interruption purpose before automatic dismissal."""
    # Provide a modal close control around task-relevant filter content.
    selected = find_dismissible_interruption([_control(overlay_context="Filter results by date and category")], "filter recent results")
    # The agent must decide how to use this task dialog.
    assert selected is None
