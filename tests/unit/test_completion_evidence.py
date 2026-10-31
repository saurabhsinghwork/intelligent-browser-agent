"""Exercise source-cited completion, changed-interface coverage, and current target grounding."""
# Construct small collaborators while exercising the actual production nodes.
from types import SimpleNamespace
# Check independent failure paths without browser or model network calls.
import pytest
# Verify the actual shared semantic audit.
from models.base import audit_objective
# Exercise coverage invalidation through the actual verifier.
from agent.nodes import verify_node
# Preserve real typed observations and decisions.
from domain.models import BrowserObservation, AgentDecision
# Exercise the common browser's input boundary.
from browser.base import BaseBrowserAdapter
# Inspect durable source ordering, not a mirrored serializer.
from services.evidence import EvidenceStore


# A positive label cannot make fabricated quotations into evidence.
@pytest.mark.parametrize("quote,expected", [("Original exact value: ₹42", True), ("Invented value: ₹99", False), ("", False)])
def test_completion_requires_exact_supported_quotes(quote, expected):
    """Verify quotations against captured source even when the selected model claims success."""
    # The same-model collaborator supplies a completion claim with explicit proof.
    provider = SimpleNamespace(decide=lambda *args: AgentDecision(kind="finish", expected="objective_met", value=__import__("json").dumps([quote])))
    # Preserve the actual source record that the audit must use.
    blocks = [{"url": "https://example.com", "key": "record", "text": "Original exact value: ₹42"}]
    # Ask the real audit to validate semantic proof against the source store.
    result, reason = audit_objective(provider, "Get the exact value", BrowserObservation(url="https://example.com"), blocks)
    # Fabrication fails despite a nominally successful provider reply.
    assert result is expected


# Native filtering at an unchanged URL must invalidate old traversal evidence.
def test_changed_same_url_requires_collection_again():
    """Prevent a filtered or paginated interface from reusing stale source coverage."""
    # Supply an independently observed changed interface.
    observation = BrowserObservation(url="https://example.com", text="Filtered source", fingerprint="after")
    # Return real typed post-action observation data.
    adapter = SimpleNamespace(observe=lambda: observation)
    # Mark only the previous interface state as fully traversed.
    state = {"adapter": adapter, "observation": {"url": observation.url, "text": "Old source", "fingerprint": "before"}, "decision": {"kind": "click"}, "collected_pages": {observation.url: {"complete": True}}, "last_outcome": {"success": True}, "screenshots": []}
    # Execute the actual independent verifier.
    result = verify_node(state)
    # New source must be collected before this page can establish completion.
    assert result["collected_pages"][observation.url] == {"complete": False, "dirty": True}


# Matching an observation ID does not authorize invented element references.
def test_fabricated_target_is_rejected_before_any_transport():
    """Refuse unobserved controls even when their reference looks structurally valid."""
    # Construct the common input boundary without a live browser.
    adapter = BaseBrowserAdapter()
    # Bind only one actual observed control to the current screenshot state.
    adapter._last_observation = BrowserObservation(url="https://example.com", observation_id="current", elements=[{"id_label": "actual"}])
    # A fabricated identity cannot reach evaluation, native input, or a hidden website target.
    with pytest.raises(LookupError, match="not present"):
        # Use a valid observation ID to isolate target membership validation.
        adapter.execute(AgentDecision(kind="click", target="invented", observation_id="current"))


# Pagination versions must keep separate provenance and ordered source content.
def test_replacement_states_do_not_collapse_equal_records(tmp_path):
    """Keep equal source records from different finite pages as distinct actual records."""
    # Use an owned durable store, as real extraction does.
    store = EvidenceStore(tmp_path / "states")
    # Capture three finite page states at identical source positions.
    for page in range(3):
        # Recycled elements and equal values cannot erase separate page relationships.
        store.add({"url": "https://example.com", "view_state": [str(page)], "blocks": [{"key": "same-node", "kind": "p", "text": "Repeated exact value", "x": 0, "y": 0}]}, "main", 0, 0)
    # Inspect independently stored source relationships.
    blocks = store.blocks()
    # Retain all three legitimate equal-valued records in actual state order.
    assert [block["view_state"] for block in blocks] == [["0"], ["1"], ["2"]]
    # Release the owned SQLite connection.
    store.close()

# Quota cooldown must remain cancellable rather than waiting behind another API call.
def test_stop_interrupts_provider_cooldown():
    """Stop during a provider retry delay without spending another request."""
    # Import the actual recovery node rather than reproducing its retry loop.
    from agent.nodes import recover_node
    # Record the requested cooldown without making a test sleep.
    waits = []
    # Simulate the user pressing Stop while the worker waits for quota recovery.
    event = SimpleNamespace(is_set=lambda: False, wait=lambda seconds: waits.append(seconds) or True)
    # Keep this real HTTP-style transient failure separate from browser strategy errors.
    state = {"last_error": "Decision failed: RateLimitError", "retry_delay": 17, "attempts": 0, "stop_event": event}
    # Execute production recovery with its shared cancellation boundary.
    result = recover_node(state)
    # Honor the provider's cooldown and observe Stop before another request.
    assert waits == [17] and result["stopped"] and not result["verified"]
