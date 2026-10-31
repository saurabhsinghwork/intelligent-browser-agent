"""Verify generalized goal compilation, progress, action policy, and record output."""
# Exercise the production goal compiler and measurable progress functions.
from agent.goals import action_policy, compile_goal, goal_records, measure_progress
# Supply real provider-neutral actions and observations.
from domain.models import AgentDecision, BrowserObservation


# A finite job request must become an explicit count and two constraints.
def test_finite_entity_goal_compiles_without_site_specific_code():
    """Compile count, entity, keyword, and location from ordinary task wording."""
    # Use the same natural-language structure as the observed acceptance task.
    goal = compile_goal("collect 10 jobs of python in pune from a job website")
    # Preserve a finite generalized entity objective.
    assert goal["mode"] == "collect_entities" and goal["entity"] == "job" and goal["required_count"] == 10
    # Keep task constraints available for both input and result validation.
    assert goal["constraints"] == {"keyword": "python", "location": "pune"}


# Detail wording must not be absorbed into location or subject constraints.
def test_full_detail_goal_separates_constraints_and_card_exclusion():
    """Compile a complete-detail request without treating output wording as a place name."""
    # Reproduce the task wording that previously produced `pune's complete detail`.
    goal = compile_goal("collect 10 jobs in pune's complete detail from a website. do not bring only job cards")
    # Preserve Pune alone and require expanded per-entity details.
    assert goal["constraints"] == {"location": "pune"} and goal["detail_level"] == "full"
    # A listing card is not completion evidence for this mode.
    card = {"kind": "li", "entity_key": "site:1", "text": "Engineer\nCompany\nPune"}
    # An exact expanded detail aggregate is valid evidence.
    detail = {"kind": "record", "entity_key": "site:1", "text": "Engineer\nCompany\nPune\nComplete description and requirements", "detail_complete": True}
    # Only the expanded source record may advance progress.
    assert goal_records([card, detail], goal) == [detail]


# Reverse subject/location phrasing must retain two independent constraints.
def test_reverse_full_detail_wording_extracts_keyword_and_location():
    """Parse `jobs in location of subject` without including detail instructions."""
    # Use the alternate wording from the preceding failed run.
    goal = compile_goal("collect 10 complete jobs in pune of python with complete details")
    # Keep both task constraints and full-detail level exact.
    assert goal["constraints"] == {"location": "pune", "keyword": "python"} and goal["detail_level"] == "full"


# Equal locations across different records must remain while one record cannot repeat.
def test_goal_records_deduplicate_entities_not_equal_field_values():
    """Retain legitimate repeated values across records and remove repeat captures."""
    # Compile a small finite objective independent of one website implementation.
    goal = compile_goal("find 2 jobs of python in pune")
    # Supply two real entities plus a repeated capture of the first one.
    blocks = [
        {"kind": "li", "entity_key": "site:100001", "text": "Python Engineer\nCompany A\nPune"},
        {"kind": "li", "entity_key": "site:100002", "text": "Python Developer\nCompany B\nPune"},
        {"kind": "li", "entity_key": "site:100001", "text": "Python Engineer\nCompany A\nPune"},
    ]
    # Logical entity identity removes only the repeated capture.
    records = goal_records(blocks, goal)
    # Both legitimate Pune values remain associated with their separate jobs.
    assert [record["entity_key"] for record in records] == ["site:100001", "site:100002"]
    # Measured completion follows unique valid entities rather than screenshot count.
    assert measure_progress(goal, blocks)["complete"] is True


# The information-only arbiter must stop signup and constraint drift.
def test_action_policy_blocks_join_and_wrong_location():
    """Reject consequential controls and fills that contradict the compiled goal."""
    # Retain two concrete observed controls from an arbitrary website.
    observation = BrowserObservation("https://example.com", elements=[{"id_label": "join", "text": "Join now", "context": "Create account"}, {"id_label": "where", "text": "Location", "context": "Where"}])
    # Compile the active requested location.
    goal = compile_goal("find 10 jobs of python in pune")
    # Joining is outside the read-only information-gathering plan.
    assert action_policy(AgentDecision(kind="click", target="join"), observation, goal)
    # Replacing Pune with an unrelated place is an explicit constraint violation.
    assert action_policy(AgentDecision(kind="fill", target="where", value="Kakori"), observation, goal)
    # Restoring the requested place remains a valid plan action.
    assert action_policy(AgentDecision(kind="fill", target="where", value="Pune"), observation, goal) == ""
