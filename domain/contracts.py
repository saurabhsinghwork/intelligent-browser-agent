"""Structural protocols for the shared model and browser boundaries.

Providers normalize multimodal decisions. Executors own actual browser I/O while
LangGraph, extraction, and supervision retain orchestration responsibilities.
"""
# Express interchangeable collaborators without requiring inheritance.
from typing import Protocol, Any
# Share typed source observations and constrained decisions.
from domain.models import AgentDecision, BrowserObservation


# Normalize either fixed multimodal provider behind one reasoning interface.
class ModelProvider(Protocol):
    """Return a grounded action without owning browser execution or source rewriting."""

    # Both text and image evidence arrive through the same observation record.
    def decide(self, task: str, observation: BrowserObservation, history: list[dict[str, Any]]) -> AgentDecision:
        """Choose one validated action from task, current source/images, and recent effects."""
        # Concrete Gemini/Groq transports implement the request and response mapping.
        ...


# Require every execution method to expose the same logical browser operations.
class BrowserAdapter(Protocol):
    """Own browser session I/O, exact targets, measurement, artifacts, and cleanup."""

    # Configure an isolated local session under the requested visibility mode.
    def initialize(self, site: str, headful: bool, session_reference: str | None = None) -> None:
        """Open the selected site after installing exact-host navigation policy."""
        # Concrete methods preserve their selected transport rather than substituting another.
        ...

    # Capture current actual visual and structured evidence.
    def observe(self) -> BrowserObservation:
        """Return current text, stable controls, geometry, tabs, and immutable screenshot."""
        # Live implementations require a real saved viewport image.
        ...

    # Execute one already validated browser operation.
    def execute(self, decision: AgentDecision) -> dict[str, Any]:
        """Return actual input/measurement effects or raise a typed blocker."""
        # Tool completion is not itself verified task success.
        ...

    # Provide deterministic source/scroll inspection for complete traversal.
    def probe(self, mode: str = "observe", **arguments) -> dict[str, Any]:
        """Read exact blocks or measure/scroll the explicitly identified container."""
        # Application-owned scripts keep mechanical collection off the model decision loop.
        ...

    # Expose actual current browser contexts.
    def manage_tabs(self) -> list[dict[str, Any]]:
        """Return real tab identities and active context without guessing index zero."""
        # Each method owns its own tab execution API.
        ...

    # Honor cancellation between local collection and transport calls.
    def check_cancelled(self) -> None:
        """Raise InterruptedError before another automatic action after Stop."""
        # Concrete supervisors provide the actual shared cancellation signal.
        ...

    # Release only this run's actual runtime resources.
    def close_or_detach(self) -> None:
        """Close owned processes while retaining eligible reusable profile state."""
        # Global browser kills and unverified recursive profile deletion are prohibited.
        ...
