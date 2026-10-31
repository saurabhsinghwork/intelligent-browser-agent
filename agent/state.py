"""Explicit serializable channels for the shared checkpointed LangGraph cycle.

Browser handles, provider clients, credentials, and synchronization objects belong
to runtime context. Error/outcome channels must survive actual node transitions.
"""
# Describe state independently of provider SDKs and browser libraries.
from typing import TypedDict, Any


# Persist only task/evidence/lifecycle data between graph cycles.
class AgentState(TypedDict, total=False):
    """Carry declared navigation, recovery, coverage, and assistance state."""
    # Preserve the user's original objective.
    task: str
    # Retain the compiled entity/count/constraint completion contract.
    goal: dict[str, Any]
    # Preserve the ordered provider-neutral task plan.
    plan: list[dict[str, Any]]
    # Track measured goal advancement independently from page changes.
    progress: dict[str, Any]
    # Prevent repeated ineffective actions in the same observed page state.
    action_memory: list[dict[str, Any]]
    # Retain the explicitly selected starting destination.
    selected_site: str
    # Record exact additional hostnames the user authorized.
    authorized_external_domains: list[str]
    # Identify the selected provider without its credential.
    model_provider: str
    # Identify the sole selected execution transport.
    browser_method: str
    # Record current browser visibility.
    headful: bool
    # Retain one current observation and immutable screenshot reference.
    observation: dict[str, Any]
    # Reuse a fresh verification observation rather than reading the page twice.
    observation_ready: bool
    # Preserve the validated current decision.
    decision: dict[str, Any]
    # Retain compact action and failure history.
    history: list[dict[str, Any]]
    # Count total failed attempts for the unresolved logical problem.
    attempts: int
    # Preserve actual diagnostics across graph nodes.
    last_error: str
    # Honor transient API quota/server cooldowns without hiding Stop.
    retry_delay: float
    # Preserve execution evidence independently of provider claims.
    last_outcome: dict[str, Any]
    # Expose current lifecycle progress.
    status: str
    # Retain safe chronological diagnostics.
    logs: list[dict[str, Any]]
    # Preserve immutable current-run viewport images.
    screenshots: list[str]
    # Store only assembled source-backed text.
    output: str
    # Keep blockers separate from available partial information.
    blocker: str
    # Distinguish cancellation from successful completion.
    stopped: bool
    # Mark only terminal outcomes.
    finished: bool
    # Treat model finish as a proposal requiring evidence.
    candidate_finish: bool
    # Record actual source/coverage verification.
    verified: bool
    # Freeze automatic work while awaiting a concrete user decision.
    waiting: dict[str, Any]
    # Retain measured page coverage independently of raw source blocks.
    collected_pages: dict[str, Any]
    # Queue actual task-relevant destinations in source order.
    frontier: list[str]
    # Prevent repeating already collected pages.
    visited: list[str]
    # Retain all discovered links beyond bounded prompt limits.
    discovered_links: list[dict[str, Any]]
    # Account for each reviewed relevance candidate.
    reviewed_links: list[str]
    # Bind model link selection to the actual supplied batch.
    link_batch: list[dict[str, Any]]
    # Apply a limit only when explicitly selected by the user.
    scroll_limit: int
    # Reference complete source exports without embedding them in monitoring events.
    artifacts: dict[str, str]
    # Stop repeated nominally successful no-op cycles without a global task cutoff.
    stagnant: int
