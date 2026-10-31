"""Redact credentials and construct safe chronological monitoring events.

Event messages may cross a worker-process boundary and be written to local logs.
Redaction happens here before those messages become user-visible diagnostics.
"""
# Import regular expressions for secret redaction patterns.
import re
# Import UTC timestamp support.
from datetime import datetime, timezone
# Import the shared event record.
from domain.models import RunEvent
# Redact credentials, auth headers, and secrets before events are emitted.
def redact_secrets(text: str) -> str:
    """Sanitize strings by redacting API keys, authorization tokens, and credentials.

    Args: text: Raw message or diagnostic string.
    Returns: Sanitized string with sensitive tokens masked.
    Side effects: None.
    Failure cases: None; non-string inputs are converted to string.
    """
    # Guard against non-string inputs.
    sanitized = str(text)
    # Redact Google GenAI API keys matching AIza pattern.
    sanitized = re.sub(r"AIza[0-9A-Za-z-_]{20,}", "[REDACTED_GEMINI_KEY]", sanitized)
    # Redact Groq API keys starting with gsk_.
    sanitized = re.sub(r"gsk_[0-9A-Za-z]{30,}", "[REDACTED_GROQ_KEY]", sanitized)
    # Redact standard HTTP Bearer tokens.
    sanitized = re.sub(r"(?i)bearer\s+[A-Za-z0-9_\-\.]{10,}", "Bearer [REDACTED_TOKEN]", sanitized)
    # Redact URL query parameters carrying credentials or secret tokens.
    sanitized = re.sub(r"(?i)(api[-_]?key|key|token|auth|secret|password)=([^&\s]+)", r"\1=[REDACTED]", sanitized)
    # Redact Authorization, Cookie, and Set-Cookie HTTP headers.
    sanitized = re.sub(r"(?i)(authorization|cookie|set-cookie):\s*([^\r\n]+)", r"\1: [REDACTED]", sanitized)
    # Return the sanitized string safe for logging and UI display.
    return sanitized
# Create an event with a stable UTC timestamp and guaranteed secret redaction.
def make_event(level: str, message: str) -> RunEvent:
    """Create a timestamped monitoring event; automatically redacts secrets from message."""
    # Redact any accidental credentials or secret tokens from the event message.
    safe_message = redact_secrets(message)
    # Use timezone-aware UTC timestamps for deterministic chronological ordering.
    return RunEvent(timestamp=datetime.now(timezone.utc).isoformat(), level=level.upper(), message=safe_message)
