"""Typed recoverable browser conditions shared by agent, adapters, and UI.

These exceptions describe a concrete next step without treating a blocked page as
task success. They carry only safe prompt data, not provider credentials.
"""


# Pause before a proposed navigation changes the authorized exact hostname.
class AuthorizationRequired(PermissionError):
    """Carry the URL that needs an explicit run-scoped hostname grant."""

    # Retain a destination for controlled authorization and resumption.
    def __init__(self, url):
        """Store the requested URL and expose a short actionable diagnostic."""
        # Preserve the original destination for a later authorized retry.
        self.url = url
        # Keep the exception message independent from secret-bearing SDK payloads.
        super().__init__("Hostname change requires explicit authorization: " + url)


# Stop automatic input while a person resolves authentication or verification.
class AssistanceRequired(RuntimeError):
    """Describe login, CAPTCHA, or another explicit user decision."""

    # Keep typed assistance data separate from ordinary retry errors.
    def __init__(self, reason, details=None):
        """Record the assistance reason and optional serializable prompt data."""
        # Identify the required intervention for the Streamlit controls.
        self.reason = reason
        # Store only the concrete decision or browser destination.
        self.details = details or {}
        # Use a concise diagnostic that the worker can display safely.
        super().__init__(reason)


# Authentication, unavailable models, or invalid request configuration cannot be fixed by clicking.
class ProviderConfigurationError(RuntimeError):
    """Report a selected-provider setup blocker without repeatedly spending API requests."""

    # Preserve only an actionable public model/status description.
    def __init__(self, provider, model, status):
        """Construct a safe error without retaining a raw response or credential."""
        # Keep model-access failures explicit instead of silently changing providers.
        super().__init__(f"{provider} model {model} returned configuration/access status {status}; check the selected API key and model access.")
