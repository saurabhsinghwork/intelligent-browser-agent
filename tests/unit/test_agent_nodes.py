"""Tests for agent node behavior on cancellation and recoverable browser failures."""
# Import a thread-safe event used by the run controller.
from threading import Event
# Import normalized records and node functions.
from domain.models import AgentDecision, BrowserObservation
from agent.nodes import observe_node, decide_node, act_node, recover_node

# A fake adapter returns observations or raises controlled errors.
class FakeAdapter:
    """Provide deterministic browser behavior for node-level tests."""
    def __init__(self, fail_observe=False, fail_execute=False):
        self.fail_observe = fail_observe
        self.fail_execute = fail_execute
    def observe(self):
        if self.fail_observe:
            raise TimeoutError("Bearer sensitive-token-value-123456")
        return BrowserObservation(url="https://example.com", text="Demo page")
    def execute(self, decision):
        if self.fail_execute:
            raise TimeoutError("Bearer sensitive-token-value-123456")
        return {"success": True}

# Cancellation should stop observation before any browser interaction.
def test_observe_honors_stop_event():
    # Arrange a set cancellation event and an adapter that would otherwise fail.
    stop_event = Event()
    stop_event.set()
    state = {"adapter": FakeAdapter(fail_observe=True), "stop_event": stop_event}
    # Act and assert the node returns a terminal stopped state.
    result = observe_node(state)
    assert result["stopped"] is True
    assert result["finished"] is True

# Browser errors should be returned to graph routing instead of escaping the node.
def test_observation_failure_becomes_recoverable_state():
    # Arrange an adapter that fails during observation.
    state = {"adapter": FakeAdapter(fail_observe=True), "screenshots": [], "stop_event": Event()}
    # Act and assert the error is normalized without the raw exception message.
    result = observe_node(state)
    # Preserve useful failure type while redacting actual credential-shaped details.
    assert result["last_error"].startswith("Observation failed: TimeoutError")
    # The specific secret must never appear in recovery context or diagnostics.
    assert "sensitive-token-value" not in result["last_error"]

# Failed actions should be routed to recovery without being added to successful history.
def test_action_failure_preserves_recovery_path():
    # Arrange a valid click decision and a failing adapter.
    state = {"adapter": FakeAdapter(fail_execute=True), "decision": AgentDecision(kind="click", target="e2").__dict__, "history": [], "stop_event": Event()}
    # Act and assert the action error is represented as graph state.
    result = act_node(state)
    # Keep actionable failure type rather than erasing every browser diagnostic.
    assert result["last_error"].startswith("Action failed: TimeoutError")
    # Actual secret-bearing details remain redacted.
    assert "sensitive-token-value" not in result["last_error"]
    assert "history" not in result

# Recovery should count attempts and preserve a bounded diagnostic.
def test_recovery_counts_attempt_and_sanitizes_message():
    # Arrange a first failed decision with a sensitive raw error omitted by node normalization.
    state = {"attempts": 0, "last_error": "Action failed: TimeoutError", "logs": []}
    # Act and assert the retry count and safe event are retained.
    result = recover_node(state)
    assert result["attempts"] == 1
    assert "Action failed: TimeoutError" in result["logs"][0]["message"]
    assert result["history"][0]["failure_type"] == "timeout"

# Verify node should confirm candidate finish when output is present.
def test_verify_node_confirms_completion():
    # Import verify_node function.
    from agent.nodes import verify_node
    # Arrange an adapter and state with candidate finish and output.
    # Valid completion requires exact source output and independently complete coverage.
    state = {"adapter": FakeAdapter(), "candidate_finish": True, "output": "Demo page", "collected_pages": {"https://example.com": {"complete": True}}, "screenshots": [], "stop_event": Event()}
    # Act and assert completion is verified.
    result = verify_node(state)
    assert result["finished"] is True
    assert result["verified"] is True
    # The completion status reflects evidence rather than nonempty answer text.
    assert "source" in result["status"].lower()

# Finite record counts and constraints are deterministic completion evidence.
def test_verify_node_accepts_source_backed_finite_goal_without_model_reassessment():
    """Do not let a second model opinion demote an already measured finite result."""
    # Import the production verifier locally with the other completion test.
    from agent.nodes import verify_node
    # Provide only the exact output interface used during final assembly.
    store = type("Store", (), {"text": lambda self, goal=None: "Python Developer\nPune"})()
    # Make any unexpected semantic model call fail the test immediately.
    provider = type("Provider", (), {"decide": lambda self, *args: (_ for _ in ()).throw(AssertionError("finite goal must not be re-audited"))})()
    # Reuse a current observation so verification performs no unrelated browser work.
    observation = BrowserObservation(url="https://example.com/jobs", text="Python Developer\nPune")
    # Supply independently measured goal, progress, and collection certificates.
    state = {"adapter": FakeAdapter(), "provider": provider, "store": store, "task": "collect 1 python job in pune", "goal": {"mode": "collect_entities", "required_count": 1}, "progress": {"complete": True}, "candidate_finish": True, "decision": {"output": ""}, "observation": observation.__dict__, "observation_ready": True, "output": "", "collected_pages": {"https://example.com/jobs": {"complete": True, "task_complete": True}}, "frontier": [], "screenshots": [], "stop_event": Event()}
    # Verify through deterministic evidence rather than another model response.
    result = verify_node(state)
    # The measured finite objective must finish successfully.
    assert result["finished"] is True and result["verified"] is True


# In a multi-cycle finite run, earlier pages may be partial while total progress is complete.
def test_verify_node_accepts_finite_goal_with_multi_cycle_pages():
    """Verify that earlier partial cycle pages do not block finite goal verification when progress is complete."""
    from agent.nodes import verify_node
    store = type("Store", (), {"text": lambda self, goal=None: "Python Developer 1\nPython Developer 2"})()
    observation = BrowserObservation(url="https://example.com/jobs?page=2", text="Python Developer 2")
    state = {
        "adapter": FakeAdapter(),
        "store": store,
        "task": "collect 2 python jobs",
        "goal": {"mode": "collect_entities", "required_count": 2},
        "progress": {"complete": True, "valid_records": 2},
        "candidate_finish": True,
        "decision": {"output": ""},
        "observation": observation.__dict__,
        "observation_ready": True,
        "output": "",
        "collected_pages": {
            "https://example.com/jobs?page=1": {"complete": False, "task_complete": False},
            "https://example.com/jobs?page=2": {"complete": True, "task_complete": True}
        },
        "frontier": [],
        "screenshots": [],
        "stop_event": Event()
    }
    result = verify_node(state)
    assert result["finished"] is True
    assert result["verified"] is True
    assert "source" in result["status"].lower()



# A stale generated identity may be repaired only from one exact quoted current label.
def test_decide_node_repairs_unique_quoted_control_target():
    """Use the current DOM identity when a rationale uniquely names the visible control."""
    # Return a stale target while explicitly naming the intended current control.
    provider = type("Provider", (), {"decide": lambda self, *args: AgentDecision(kind="click", target="old-id", rationale="Click the 'Show more' button")})()
    # Supply one unique currently actionable control with that exact label.
    observation = BrowserObservation(url="https://example.com/results", observation_id="current", elements=[{"id_label": "fresh-id", "text": "Show more", "aria_label": "Show more", "in_view": True, "actionable": True}])
    # Keep navigation and progress state empty so ordinary action selection runs.
    state = {"provider": provider, "task": "collect complete details", "observation": observation.__dict__, "history": [], "goal": {}, "plan": [], "progress": {}, "action_memory": [], "discovered_links": [], "reviewed_links": [], "visited": [], "frontier": [], "collected_pages": {}}
    # Execute the shared decision grounding stage.
    result = decide_node(state)
    # Only the current exact DOM identity may reach browser execution.
    assert result["decision"]["target"] == "fresh-id" and result["decision"]["observation_id"] == "current"


# A full-detail planner must not repeatedly rescan one unchanged listing scope.
def test_decide_node_rejects_repeated_zero_progress_collect():
    """Force replanning when an identical collection already produced no objective progress."""
    # Return the same broad collection that failed to advance during the real regression.
    provider = type("Provider", (), {"decide": lambda self, *args: AgentDecision(kind="collect", target="main", rationale="Collect the visible detail")})()
    # Bind the decision to one unchanged search-results page state.
    observation = BrowserObservation(url="https://example.com/search?q=python", fingerprint="same-listing")
    # Preserve the prior measured no-progress collection in bounded action memory.
    memory = [{"kind": "collect", "target": "main", "value": "", "page": "https://example.com/search?q=python", "fingerprint": "same-listing", "advanced": False}]
    # Supply the ordinary decision context without invoking a browser action.
    state = {"provider": provider, "task": "collect complete details", "observation": observation.__dict__, "history": [], "goal": {"detail_level": "full"}, "plan": [], "progress": {}, "action_memory": memory, "discovered_links": [], "reviewed_links": [], "visited": [], "frontier": [], "collected_pages": {}}
    # Run shared grounding and no-progress policy.
    result = decide_node(state)
    # The repeated scan must become a strategy failure instead of another 27-scroll traversal.
    assert "already failed to advance" in result["last_error"]


# A finish proposal must not re-trigger collection if the goal is already complete.
def test_act_node_finish_skips_collect_when_goal_complete():
    """Ensure finish proposals do not re-run collection even if URL appears uncollected."""
    state = {
        "decision": {"kind": "finish", "target": "", "rationale": "Measured completion reached", "expected": "objective_met", "output": ""},
        "observation": {"url": "https://example.com/jobs?currentJobId=123", "text": "Jobs page"},
        "progress": {"complete": True, "valid_records": 10},
        "collected_pages": {"https://example.com/jobs": {"complete": True}},
        "task": "collect 10 jobs",
        "stop_event": Event()
    }
    result = act_node(state)
    # Must immediately prepare to finish without re-collecting.
    assert result["candidate_finish"] is True
    assert result["last_outcome"]["action"] == "collect"
    # Should not have populated collected_pages with a new key.
    assert "collected_pages" not in result or len(result.get("collected_pages", {})) == 0


# When collection satisfies the goal, candidate_finish must be True immediately.
def test_act_node_collect_sets_candidate_finish_when_progress_complete():
    """Ensure act_node signals candidate_finish=True as soon as progress is complete."""
    # Mock adapter that returns progress complete during collection
    class CollectorAdapter:
        def probe(self, *args, **kwargs):
            return {
                "url": "https://example.com/jobs",
                "blocks": [{"title": "Eng", "company": "Co", "text": "Python Engineer Pune", "detail_complete": True}],
                "links": [],
                "containers": [],
                "limitations": [],
                "complete": True,
                "task_complete": True
            }
        def observe(self, *args, **kwargs):
            return BrowserObservation(url="https://example.com/jobs", text="Jobs page")
        def _evaluate(self, script):
            return {}

    class MockStore:
        def blocks(self):
            return [{"title": "Eng", "company": "Co", "text": "Python Engineer Pune", "kind": "record", "detail_complete": True}]
        def export(self, goal):
            return {}
        def text(self, goal):
            return "Sample job text"
        def page(self, *args, **kwargs):
            pass
        def add(self, *args, **kwargs):
            pass

    state = {
        "decision": {"kind": "collect", "target": "body", "rationale": "Collect jobs", "expected": "", "output": ""},
        "observation": {"url": "https://example.com/jobs", "text": "Jobs page"},
        "adapter": CollectorAdapter(),
        "store": MockStore(),
        "goal": {"mode": "collect_entities", "required_count": 1},
        "progress": {"complete": False},
        "collected_pages": {},
        "task": "collect 1 job",
        "stop_event": Event()
    }
    result = act_node(state)
    # The progress achieved should immediately set candidate_finish to True.
    assert result["candidate_finish"] is True
    assert result["progress"]["complete"] is True

