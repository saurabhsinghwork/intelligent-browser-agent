"""Gemini 3.5 Flash-Lite text/image transport for shared browser reasoning.

This module owns SDK requests and response mapping. It never changes the model,
executes browser commands, or replaces empty-output actions with task success.
"""
# Reuse provider-neutral prompts, structured schema, and action validation.
from models.base import DECISION_SCHEMA, decision_schema, decision_prompt, parse_decision, screenshot_files
# Keep untrusted page content below explicit system-level task rules.
from agent.prompts import AGENT_RULES
# Stop configuration failures without retrying browser navigation.
from domain.errors import ProviderConfigurationError
# Fix the model the user can access; no silent fallback is permitted.
GEMINI_MODEL = "gemini-3.5-flash-lite"


# Retain one lazy selected-provider client for the run.
class GeminiProvider:
    """Return one grounded action using both screenshots and structured browser state."""

    # Accept injected clients so transport contracts can be tested without credentials.
    def __init__(self, api_key: str, client=None):
        """Store runtime-only credentials and an optional client without calling the API."""
        # Keep the credential outside graph state, events, and persisted checkpoints.
        self._api_key = api_key
        # Reuse this client across decisions instead of reconnecting per scroll.
        self._client = client

    # Request the next action with actual local screenshot bytes.
    def decide(self, task, observation, history):
        """Return a validated decision; expose SDK/format failures without substituting models."""
        # Import the SDK only when Gemini is selected.
        from google import genai
        # Use installed request types for images, timeout, and constrained JSON.
        from google.genai import types
        # Create a bounded-timeout client once for this run.
        if self._client is None:
            # Google HttpOptions expresses request deadlines in milliseconds.
            self._client = genai.Client(api_key=self._api_key, http_options=types.HttpOptions(timeout=45000, retry_options=types.HttpRetryOptions(attempts=1)))
        # Start with exactly the shared navigation context used by Groq.
        contents = [decision_prompt(task, observation, history)]
        # Read only current relevant PNG evidence.
        for path in screenshot_files(observation):
            # Send image bytes rather than a filesystem path disguised as visual context.
            contents.append(types.Part.from_bytes(data=path.read_bytes(), mime_type="image/png"))
        # Ask the fixed supported model for schema-constrained JSON.
        try:
            # Keep page text untrusted through an actual system instruction.
            response = self._client.models.generate_content(model=GEMINI_MODEL, contents=contents, config=types.GenerateContentConfig(system_instruction=AGENT_RULES, response_mime_type="application/json", response_json_schema=decision_schema(task, observation), temperature=0))
        # Invalid access cannot be corrected through repeated browser actions.
        except Exception as exc:
            # The Google SDK exposes HTTP status as code.
            status = getattr(exc, "code", None)
            # Authentication/model/schema failures require explicit setup correction.
            if status in {400, 401, 403, 404}:
                # Do not preserve a raw response that could contain secret values.
                raise ProviderConfigurationError("Gemini", GEMINI_MODEL, status) from exc
            # Transient errors remain available to the shared bounded recovery policy.
            raise
        # Preserve valid click/fill/scroll/blocked decisions even when output is empty.
        return parse_decision(response.text or "{}")
