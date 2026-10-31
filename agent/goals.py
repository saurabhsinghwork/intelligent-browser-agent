"""Compile user instructions into generalized goals, plans, and progress facts.

The compiler supplies deterministic minimum structure for every model/provider. The
selected model still resolves ambiguous interfaces, while application code enforces
counts, constraints, forbidden actions, and measurable completion.
"""
# Preserve plan/goal records as ordinary JSON-safe dictionaries.
from dataclasses import asdict, dataclass, field
# Extract explicit counts and common natural-language constraint phrases.
import re


# Describe one generalized information-gathering objective.
@dataclass(frozen=True)
class GoalSpec:
    """Store the requested entity, count, constraints, fields, and completion mode."""
    # Retain the user's instruction verbatim for model context and auditing.
    objective: str
    # Name the logical record type without binding execution to one website.
    entity: str = "record"
    # Stop after this many validated unique records when the user supplied a count.
    required_count: int | None = None
    # Preserve exact task constraints as normalized comparison values.
    constraints: dict[str, str] = field(default_factory=dict)
    # Retain explicitly requested output fields when they can be identified.
    requested_fields: list[str] = field(default_factory=list)
    # Distinguish finite record gathering from complete page/site traversal.
    mode: str = "information"
    # Require expanded per-entity source rather than accepting listing-card summaries when requested.
    detail_level: str = "summary"
    # Keep the initial release within read-only information gathering.
    forbidden_actions: list[str] = field(default_factory=lambda: ["join", "sign up", "register", "apply", "subscribe", "purchase", "checkout", "send", "delete", "set alert"])
    # Specialized domain execution strategy (e.g. linkedin or standard).
    strategy: str = "standard"
    # Resolved direct starting URL if query parameters are identifiable.
    direct_url: str = ""
    # Disambiguated human-readable objective.
    clarified_objective: str = ""


# Recognize broad record nouns without introducing website-specific behavior.
_ENTITY_WORDS = ("jobs", "products", "items", "records", "results", "articles", "courses", "hotels", "flights", "restaurants", "companies", "people", "posts", "videos")
# Recognize common exact output fields while preserving unknown task text for the model.
_FIELD_WORDS = ("title", "company", "location", "price", "rating", "date", "salary", "description", "url", "link", "availability", "name")


# Compile a useful typed objective before the first browser/model cycle.
def compile_goal(task):
    """Return a JSON-safe generalized goal derived from the original instruction."""
    # Preserve the exact instruction while using lowercase text only for matching.
    original = str(task or "").strip()
    # Normalize case without rewriting source wording.
    lowered = original.lower()
    # Extract an explicit finite count near a record noun when supplied.
    counted = re.search(r"\b(?:at\s+least\s+)?(\d+)\s+([a-z][a-z -]{0,30})", lowered)
    # Default to an unbounded information objective.
    required_count = int(counted.group(1)) if counted else None
    # Select the first recognized entity word present in the instruction.
    entity = next((word for word in _ENTITY_WORDS if re.search(r"\b" + re.escape(word) + r"\b", lowered)), "records")
    # Singularize only a conventional trailing s for readable plan text.
    singular = entity[:-1] if entity.endswith("s") else entity
    # Begin with no inferred constraints.
    constraints = {}
    # Detect an explicit request for complete per-record information rather than listing cards.
    full_details = bool(re.search(r"\b(?:complete|full|detailed)\s+(?:record\s+)?details?\b|\bnot\s+(?:only|just)\s+(?:the\s+)?(?:job\s+)?cards?\b", lowered))
    # Parse common "jobs/products of X in Y" phrasing without naming a website.
    subject_location = re.search(r"\b" + re.escape(entity) + r"\s+(?:of|for|about)\s+(.+?)\s+(?:in|near|at)\s+([a-z][a-z .'-]+?)(?:\s+(?:from|on|with|having)\b|$)", lowered)
    # Preserve a subject keyword when the phrase is sufficiently concrete.
    if subject_location:
        # Store the requested subject independently from the entity noun.
        constraints["keyword"] = subject_location.group(1).strip()
        # Store the requested place independently for later input/result validation.
        constraints["location"] = subject_location.group(2).strip()
    # Fall back to an explicit location phrase when no subject-location pair matched.
    elif entity != "records":
        # Read a short location value after an `in` or `near` constraint.
        location = re.search(r"\b(?:in|near)\s+([a-z][a-z .'-]{1,50}?)(?:\s+(?:from|on|with|having|under|over)\b|$)", lowered)
        # Retain the concrete location only when present.
        if location:
            # Remove output-detail wording and reverse `location of subject` phrasing.
            location_value = re.split(r"(?:'s)?\s+(?:complete|full|detailed)\s+(?:record\s+)?details?\b|\s+(?:of|for)\s+", location.group(1).strip(), maxsplit=1)[0].strip(" ,.'")
            # Retain only the concrete place rather than adjacent output requirements.
            constraints["location"] = location_value
    # Support common reverse phrasing such as `jobs in Pune of Python`.
    reverse_subject = re.search(r"\b" + re.escape(entity) + r"\s+(?:in|near|at)\s+[a-z][a-z .'-]*?\s+(?:of|for)\s+(.+?)(?:\s+(?:with|from|on|having)\b|$)", lowered)
    # Preserve the reverse subject only when the task actually supplied one.
    if reverse_subject and reverse_subject.group(1).strip() not in {"complete detail", "complete details", "full detail", "full details"}:
        # Keep the subject independent from location and detail wording.
        constraints.setdefault("keyword", reverse_subject.group(1).strip())
    # Support adjective-before-entity phrasing such as `10 Python jobs in Pune`.
    before_entity = re.search(r"\b(?:at\s+least\s+)?\d+\s+(?:(?:complete|full|detailed)\s+)?([a-z0-9+#.-]+)\s+" + re.escape(entity) + r"\b", lowered)
    # Do not invent a subject when the count is followed directly by the entity noun.
    if before_entity and before_entity.group(1) not in {"complete", "full", "detailed"}:
        # Retain the explicitly supplied subject keyword.
        constraints.setdefault("keyword", before_entity.group(1))
    # Collect only field names the user actually mentioned.
    fields = [field_name for field_name in _FIELD_WORDS if re.search(r"\b" + re.escape(field_name) + r"\b", lowered)]
    # Refine task using intelligent query refiner.
    from agent.refiner import refine_task
    # Understand user instruction and disambiguate intent.
    refinement = refine_task(original)
    # Merge refined strategy when identified.
    strategy = refinement.get("strategy", "standard")
    # Merge full detail mode when recognized by refiner.
    if refinement.get("detail_level") == "full":
        # Require expanded per-entity details.
        full_details = True
    # Merge extracted constraints.
    for k, v in refinement.get("constraints", {}).items():
        # Preserve specific constraints.
        constraints.setdefault(k, v)
    # Use refined count when not matched by simple regex.
    if refinement.get("required_count") and not required_count:
        # Assign refined count.
        required_count = refinement["required_count"]
    # Retain direct search URL if applicable.
    direct_url = refinement.get("direct_url", "")
    # Retain clarified objective.
    clarified_objective = refinement.get("clarified_objective", original)
    # A finite entity count uses record collection rather than exhaustive site traversal.
    mode = "collect_entities" if required_count and entity != "records" else ("page" if re.search(r"\b(?:this|that|current|selected)\s+page\b|\bpage\s+only\b", lowered) else "information")
    # Construct one immutable goal and expose it as checkpoint-safe data.
    goal = GoalSpec(objective=original, entity=singular, required_count=required_count, constraints=constraints, requested_fields=fields, mode=mode, detail_level="full" if full_details else "summary", strategy=strategy, direct_url=direct_url, clarified_objective=clarified_objective)
    # Return declared fields only.
    return asdict(goal)


# Build a short plan that remains stable across model navigation cycles.
def build_plan(goal):
    """Return provider-neutral steps with measurable completion conditions."""
    # Read goal values defensively from persisted state.
    entity = goal.get("entity", "record")
    # Describe the finite target when available.
    count = goal.get("required_count")
    # Preserve exact constraints for UI-state and result validation.
    constraints = goal.get("constraints", {})
    # Tailor plan steps for specialized domain strategies.
    if goal.get("strategy") == "linkedin":
        # Create LinkedIn master-detail plan steps.
        steps = [
            {"id": "reach_subject", "purpose": "Reach the LinkedIn jobs search interface.", "success": "The current DOM contains task-relevant LinkedIn job cards or controls."},
            {"id": "apply_constraints", "purpose": "Apply and verify search parameters: " + str(constraints) + ".", "success": "Observed results match the requested role and location."},
            {"id": "collect_records", "purpose": "Execute master-detail traversal: iterate cards, expand full descriptions, and collect complete records with 1-line overlap scrolling.", "success": (str(count) + " unique valid full job records are stored.") if count else "Collection complete."},
            {"id": "verify_output", "purpose": "Validate completeness of job details, uniqueness, and constraints.", "success": "Every returned record includes full job description without hallucination."},
        ]
        # Return tailored steps.
        return steps
    # Create explicit ordered phases rather than rediscovering the task each cycle.
    steps = [
        {"id": "reach_subject", "purpose": "Reach the interface containing the requested " + entity + " information.", "success": "The current DOM contains task-relevant content or controls."},
        {"id": "apply_constraints", "purpose": "Apply and verify the requested filters or search values.", "success": "Observed inputs, URL state, or rendered results agree with " + str(constraints) + "."},
        {"id": "collect_records", "purpose": "Collect unique qualifying " + entity + " records using rendered DOM evidence.", "success": (str(count) + " unique valid records are stored.") if count else "The requested finite scope is completely traversed."},
        {"id": "verify_output", "purpose": "Validate constraints, uniqueness, and exact source wording.", "success": "Every returned record is source-backed and the completion predicate is met."},
    ]
    # Return JSON-safe plan data.
    return steps


# Identify qualifying record-like blocks without collapsing equal values across entities.
def goal_records(blocks, goal):
    """Return unique exact blocks that satisfy a finite entity goal's constraints."""
    # Non-finite objectives retain ordinary page-oriented extraction.
    if not goal or goal.get("mode") != "collect_entities":
        # No entity subset is defined for this objective.
        return []
    # Normalize constraint values for case-insensitive rendered-text checks.
    values = [str(value).strip().lower() for value in goal.get("constraints", {}).values() if str(value).strip()]
    # Prefer semantic record containers over individual labels and navigation chrome.
    record_kinds = {"li", "table_row", "article", "record"}
    # Retain first source order and stable entity uniqueness.
    selected = []
    # Track logical entities independently from equal displayed text.
    seen = set()
    # Inspect complete captured evidence in its real order.
    for block in blocks:
        # Full-detail objectives require completed full detail or full description.
        if goal.get("detail_level") == "full" and not block.get("detail_complete") and "Job Description:" not in str(block.get("text", "")):
            # Wait for a complete expanded detail region or detail page aggregate.
            continue
        # Skip headings, buttons, and generic chrome for entity output.
        if block.get("kind") not in record_kinds and not block.get("entity_key"):
            # Continue to the next source block.
            continue
        # Read exact rendered source without modifying it.
        text = str(block.get("text", ""))
        # Every explicit constraint must appear in the record's rendered text.
        if values and not all(value in text.lower() for value in values):
            # This record does not satisfy the requested subject/location combination.
            continue
        # Prefer a stable semantic entity identity (e.g. title and company for job/product records).
        # Extract lowercase company name for deduplication.
        company = str(block.get("company", "")).strip().lower()
        # Read explicit entity key if provided by strategy.
        entity_key = str(block.get("entity_key", "")).strip()
        # Read direct entity URL if provided by strategy.
        entity_url = str(block.get("entity_url", "")).strip()
        # Primary semantic identity is title and company.
        if title and company:
            # Construct composite title and company identity key.
            identity = f"record:{title}::{company}"
        # Secondary identity is specific non-search entity key.
        elif entity_key and not any(kw in entity_key.lower() for kw in ("/search", "keywords=", "query=", "q=")):
            # Use non-search entity key as identity.
            identity = entity_key
        # Tertiary identity is specific entity view URL.
        elif entity_url and not any(kw in entity_url.lower() for kw in ("/search", "keywords=", "query=", "q=")):
            # Use canonical entity target URL as identity.
            identity = entity_url
        # Fall back to structural tuple identity when semantic fields are missing.
        else:
            # Group by URL, headings, and preview prefix.
            identity = (block.get("url", ""), block.get("headings", []), text[:120])
        # Ignore only another capture of this same logical entity.
        if str(identity) in seen:
            # Preserve legitimate equal fields belonging to different entities elsewhere.
            continue
        # Record this logical entity before adding its exact source block.
        seen.add(str(identity))
        # Preserve original block metadata and wording.
        selected.append(block)
    # Return every currently qualifying unique record; callers apply the requested count.
    return selected


# Create the progress facts supplied to every later action decision.
def measure_progress(goal, blocks, previous=None):
    """Return concrete record counts, remaining work, and constraint status."""
    # Preserve a default empty previous ledger for the first measurement.
    prior = previous or {}
    # Count unique qualifying records through the same output identity rules.
    records = goal_records(blocks, goal)
    # Read an optional finite completion target.
    target = goal.get("required_count") if goal else None
    # Calculate remaining records without producing a negative value.
    remaining = max(0, int(target) - len(records)) if target else None
    # Distinguish new evidence from navigation-only activity.
    advanced = len(records) > int(prior.get("valid_records", 0))
    # Publish only compact facts suitable for checkpoints and model context.
    return {"valid_records": len(records), "required_records": target, "remaining_records": remaining, "constraints": dict(goal.get("constraints", {})) if goal else {}, "advanced": advanced, "complete": bool(target and len(records) >= int(target))}


# Enforce information-only and constraint-preserving actions before browser input.
def action_policy(decision, observation, goal):
    """Return an empty string for an allowed action or a concrete rejection reason."""
    # Only interactive decisions can activate an unrelated website control.
    if decision.kind not in {"click", "fill"}:
        # Collection, navigation, and terminal actions use their separate guards.
        return ""
    # Resolve the proposed identity only from the current observation.
    target = next((item for item in observation.elements if item.get("id_label") == decision.target), None)
    # A missing target is handled by the adapter's ordinary stale-observation check.
    if target is None:
        # Do not duplicate the more precise grounding error.
        return ""
    # Combine visible label and local context for action-intent classification.
    label = (str(target.get("text", "")) + " " + str(target.get("aria_label", "")) + " " + str(target.get("context", ""))).lower()
    # Reject every forbidden information-changing action from the compiled goal.
    for phrase in goal.get("forbidden_actions", []) if goal else []:
        # Match natural control labels without relying on one website's CSS.
        if re.search(r"\b" + re.escape(phrase.lower()) + r"\b", label):
            # Explain the exact policy conflict for replanning.
            return "Control is outside the information-gathering plan: " + phrase
    # A location input must retain the requested location rather than drifting elsewhere.
    requested_location = str((goal or {}).get("constraints", {}).get("location", "")).strip().lower()
    # Detect location-labelled inputs using DOM label/context semantics.
    location_input = decision.kind == "fill" and re.search(r"\b(location|city|where)\b", label)
    # Reject an observed fill that contradicts the compiled task constraint.
    if requested_location and location_input and requested_location not in decision.value.lower():
        # Force the model to restore the requested location.
        return "Location value conflicts with the task constraint: " + requested_location
    # The proposed information-gathering action is consistent with the current goal.
    return ""


# Decide whether automatic traversal may open a control without another model call.
def relevant_expansion(control, goal):
    """Allow only task-related expanders, result loading, and finite pagination controls."""
    # Explicit complete-page diagnostics without a compiled goal retain exhaustive behavior.
    if not goal:
        # Preserve backwards-compatible finite traversal for direct collector callers.
        return True
    # Combine rendered label and surrounding DOM context.
    text = (str(control.get("text", "")) + " " + str(control.get("context", ""))).lower()
    # Consequential controls remain forbidden during automatic collection.
    for phrase in goal.get("forbidden_actions", []) if goal else []:
        # Reject matching controls before considering generic expansion semantics.
        if re.search(r"\b" + re.escape(phrase.lower()) + r"\b", text):
            # Never open signup, application, alert, or other out-of-scope flows.
            return False
    # Complete page/article tasks inspect every remaining safe finite disclosure.
    if goal.get("mode") != "collect_entities":
        # Broad source fidelity takes precedence when no record count bounds the task.
        return True
    # Standard disclosure labels reveal existing source without changing user data.
    if re.search(r"\b(show more|read more|load more|more details|expand|see more)\b", text):
        # Permit finite source disclosure.
        return True
    # A finite result goal may use actual pagination controls to reach its count.
    if goal and goal.get("mode") == "collect_entities" and control.get("pagination"):
        # Pagination remains bounded by the explicit required record count.
        return True
    # Tabs are relevant only when their label or context shares an objective term.
    terms = {word for word in re.findall(r"[a-z0-9]+", str((goal or {}).get("objective", "")).lower()) if len(word) > 2}
    # Require at least one meaningful task term for an otherwise generic expander/tab.
    return bool(terms and any(term in text for term in terms))
