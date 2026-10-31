"""Validate constrained decisions before read-only browser execution.

Providers, custom clients, and tests all pass through the same action validation.
The browser additionally checks current target identity and exact-host permission.
"""
# Share the same supported operations as the provider response schema.
from models.base import ACTION_KINDS


# Validate runtime data rather than trusting action type hints alone.
def validate_decision(decision):
    """Raise ValueError for unsupported operations or missing required targets."""
    # Unknown commands must never reach a browser executor.
    if decision.kind not in ACTION_KINDS:
        # Keep malformed response failures explicit and recoverable.
        raise ValueError("Unsupported browser decision")
    # Navigation requires an actual destination.
    if decision.kind == "navigate" and not decision.target.strip():
        # Do not guess a website when the model omitted its URL.
        raise ValueError("Navigation decision is missing its destination.")
    # Interactive and tab operations require concrete identifiers.
    if decision.kind in {"click", "fill", "press", "switch_tab", "close_tab"} and not decision.target.strip():
        # No implicit first control or tab is allowed.
        raise ValueError(f"{decision.kind} decision is missing its target" + (" tab." if decision.kind in {"switch_tab", "close_tab"} else "."))
