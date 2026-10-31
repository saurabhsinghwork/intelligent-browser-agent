"""Tests for LangGraph routing behavior, including failures and cancellation."""
# Import pytest for assertion helpers.
import pytest
# Import graph routing helpers without requiring LangGraph at test time.
from agent.graph import _route_failure_or, _route_decision, _route_recovery

# A terminal state must stop the graph before any further action.
def test_terminal_state_routes_to_end():
    # Arrange a completed state.
    state = {"finished": True, "last_error": "ignored"}
    # Assert terminal routing has priority over recovery.
    assert _route_failure_or("decide")(state) == "end"

# Any recoverable node failure must enter the shared recovery node.
def test_failure_routes_to_recovery():
    # Arrange a state with a sanitized recoverable error.
    state = {"last_error": "Action failed: TimeoutError", "finished": False}
    # Assert the graph routes the error through the retry manager.
    assert _route_failure_or("verify")(state) == "recover"

# A valid decision should proceed to action dispatch.
def test_valid_decision_routes_to_action():
    # Arrange a normal click decision.
    state = {"decision": {"kind": "click"}, "finished": False}
    # Assert the selected adapter will receive the action.
    assert _route_decision(state) == "act"

# Exhausted recovery must terminate rather than looping forever.
def test_exhausted_recovery_routes_to_end():
    # Arrange the recovery node's terminal blocker state.
    state = {"finished": True, "blocker": "Five attempts exhausted"}
    # Assert the graph ends after the documented attempt limit.
    assert _route_recovery(state) == "end"

# A successful recovery should re-observe before asking the model again.
def test_recovery_routes_to_observation():
    # Arrange a non-terminal recovery state.
    state = {"finished": False, "attempts": 2}
    # Assert the browser state is refreshed before the next decision.
    assert _route_recovery(state) == "observe"
