"""Provider-neutral records for browser navigation, source evidence, and events.

Records contain serializable data. Compact model context is separate from complete
rendered source evidence; SDK clients and browser objects belong to runtime context.
"""
# Build explicit records without coupling them to a provider SDK.
from dataclasses import dataclass, field
# Annotate browser-specific metadata while keeping shared fields stable.
from typing import Any


# Describe an actual discovered website requiring explicit user selection.
@dataclass(frozen=True)
class WebsiteCandidate:
    """Store the search result name, exact hostname, and HTTP(S) destination."""
    # Preserve the search result's human-readable title.
    name: str
    # Keep the exact host used by navigation authorization.
    domain: str
    # Retain the actual result URL instead of inventing a domain.
    url: str


# Describe one page state and bind targets to its immutable screenshot.
@dataclass
class BrowserObservation:
    """Carry rendered text, current targets, links, geometry, and screenshot evidence.

    Text preserves formatting. Providers bound only their navigation prompt, while
    the evidence service retains complete extracted content outside model context.
    """
    # Identify the observed destination.
    url: str
    # Preserve the document title.
    title: str = ""
    # Preserve source text, indentation, and meaningful blank lines.
    text: str = ""
    # Describe current interactive elements with stable references.
    elements: list[dict[str, Any]] = field(default_factory=list)
    # Reference an immutable image rather than a repeatedly overwritten file.
    screenshot_path: str | None = None
    # Describe actual available tabs.
    tabs: list[dict[str, Any]] = field(default_factory=list)
    # Retain capture history independently of model image limits.
    all_screenshots: list[str] = field(default_factory=list)
    # Bind action references to the observation that generated them.
    observation_id: str = ""
    # Keep CSS viewport, image scale, and measured scroll containers.
    geometry: dict[str, Any] = field(default_factory=dict)
    # Preserve discovered link labels and source ordering.
    links: list[dict[str, Any]] = field(default_factory=list)
    # Compare meaningful page state before and after an action.
    fingerprint: str = ""


# Represent the constrained action language shared by both models.
@dataclass(frozen=True)
class AgentDecision:
    """Describe one browser action, collection request, assistance, or finish proposal.

    A finish proposal is never proof of completion. collect stores source evidence;
    queue_links selects relevant URLs from a bounded batch using the selected model.
    """
    # Identify one supported workflow operation.
    kind: str
    # Identify a current element, scroll container, region selector, or destination.
    target: str = ""
    # Supply search text, a key, or a scroll direction.
    value: str = ""
    # Explain the chosen action briefly without private chain-of-thought.
    rationale: str = ""
    # Optionally quote source text; generated prose is not extraction evidence.
    output: str = ""
    # Describe the expected observable effect.
    expected: str = ""
    # Bind interactive actions to their current observation.
    observation_id: str = ""
    # Select relevant URLs from the explicit link-review batch.
    links: list[str] = field(default_factory=list)


# Serialize one safe diagnostic event across the worker/UI boundary.
@dataclass(frozen=True)
class RunEvent:
    """Store timestamp, severity, and redacted message for the current run."""
    # Record an unambiguous UTC timestamp.
    timestamp: str
    # Distinguish ordinary progress, warnings, and errors.
    level: str
    # Retain safe diagnostics rather than credentials or SDK request payloads.
    message: str
