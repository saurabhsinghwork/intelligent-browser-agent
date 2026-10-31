"""Verify task-progress detection and grounded rejection of unrelated queued pages."""
# Construct strict action data without provider access.
from dataclasses import asdict
# Exercise the actual shared action handler.
from agent.nodes import act_node
# Supply normalized production actions.
from domain.models import AgentDecision
# Exercise the production cross-cycle progress guard.
from services.run_controller import navigation_cycle

# Alternating successful URLs must not count as indefinite task progress.
def test_repeated_navigation_is_detected():
    """Stop repeated arrivals but reset the guard after meaningful collection."""
    # Retain counts within one evidence epoch.
    seen = {}
    # Simulate independently observed alternating destinations.
    state = {"decision":{"kind":"navigate"},"visited":[],"reviewed_links":[],"frontier":[]}
    # First visits and one revisit remain permitted.
    for index in range(4):
        # Alternate real destinations while keeping evidence unchanged.
        state["observation"] = {"url":"https://example.com/" + ("b" if index % 2 == 0 else "a")}
        # Neither side has yet been reached three times.
        assert not navigation_cycle(state,"https://example.com/" + ("a" if index % 2 == 0 else "b"),seen)
    # The third arrival at B closes the repeated navigation cycle.
    state["observation"] = {"url":"https://example.com/b"}
    # A successful navigation cannot erase the absence of task evidence.
    assert navigation_cycle(state,"https://example.com/a",seen)
    # Actual collection establishes a fresh progress epoch.
    state["visited"] = ["https://example.com/a"]
    # Legitimate revisits after new evidence must remain possible.
    assert not navigation_cycle(state,"https://example.com/a",seen)

# Rejected pages must leave an auditable reason without fabricated source capture.
def test_reject_current_queued_page():
    """Remove only the actual observed first queued destination."""
    # Bind the rejection to the current observed page.
    state = {"decision":asdict(AgentDecision(kind="queue_links",target="skip_current",rationale="Generic home page has no operator details")),"observation":{"url":"https://example.com/"},"frontier":["https://example.com/","https://example.com/operators"],"visited":[]}
    # Apply the production scope-revision action.
    result = act_node(state)
    # The relevant destination remains queued.
    assert result["frontier"] == ["https://example.com/operators"]
    # The rejected URL remains inspectable in checkpoint history.
    assert result["history"][0]["excluded_url"] == "https://example.com/"
    # Rejection cannot falsely claim source coverage or task completion.
    assert "visited" not in result and not result["candidate_finish"]

# A model cannot use the rejection action to silently discard a different destination.
def test_rejection_requires_observed_frontier_head():
    """Reject a scope mutation when the current page is not the first queued URL."""
    # Deliberately mismatch the current observed and proposed queued destinations.
    state = {"decision":asdict(AgentDecision(kind="queue_links",target="skip_current",rationale="Not relevant")),"observation":{"url":"https://example.com/other"},"frontier":["https://example.com/"]}
    # The normal recovery path must preserve the actual queue.
    result = act_node(state)
    # No destination may be removed by this malformed response.
    assert "frontier" not in result and result["last_error"]

# A harmless extra target must not change the meaning of a concrete link-review batch.
def test_empty_link_batch_selection_does_not_reject_page():
    """Account for a rejected batch while preserving the page frontier."""
    # Reproduce the actual live model response for unrelated navigation links.
    state = {"decision":asdict(AgentDecision(kind="queue_links",target="skip_current",links=[],rationale="No links in this batch are relevant")),"link_batch":[{"url":"https://example.com/home"}],"frontier":["https://example.com/operators"],"observation":{"url":"https://example.com/current"}}
    # Batch context determines semantics before a meaningless spare target field.
    result = act_node(state)
    # Preserve the actual page queue and count every reviewed URL.
    assert result["frontier"] == ["https://example.com/operators"]
    # Repeated review must not stall on the same unrelated batch.
    assert result["reviewed_links"] == ["https://example.com/home"]
