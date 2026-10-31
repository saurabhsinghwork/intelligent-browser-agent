"""Typed, validated runtime configuration. Secrets are supplied per run and are never persisted here."""
# Import dataclass support for a compact immutable settings object.
from dataclasses import dataclass, field
# Import identifiers to validate selections against the documented options.
from config.constants import MODEL_PROVIDERS, BROWSER_METHODS
# Define the configuration shared by the UI, controller, and agent.
@dataclass(frozen=True)
class RunConfiguration:
    """Hold the mutually exclusive provider/method and visibility choices for one run."""
    # Store the selected reasoning provider.
    model_provider: str
    # Store the selected browser execution adapter.
    browser_method: str
    # Store whether the browser should be visibly rendered.
    headful: bool
    # Store the API key only for the active run; callers must not log this value.
    api_key: str = field(repr=False)
    # Validate selections and required credentials before execution.
    def validate(self) -> None:
        """Raise ValueError when the run configuration violates documented constraints."""
        # Reject providers outside the two supported choices.
        if self.model_provider not in MODEL_PROVIDERS:
            # Correct stale or ambiguous provider labels before any runtime work starts.
            raise ValueError("Select exactly one supported model provider.")
        # Reject browser methods outside the three supported choices.
        if self.browser_method not in BROWSER_METHODS:
            # No unrequested fourth method or silent executor substitution is permitted.
            raise ValueError("Select exactly one supported browser method.")
        # Require a non-empty credential for the chosen provider.
        if not self.api_key.strip():
            # Website discovery remains keyless, but task reasoning requires the selected key.
            raise ValueError("Enter an API key for the selected model provider.")
