"""Groq Qwen 3.8 27B multimodal transport for the selected reasoning provider.

Groq is not xAI Grok. The same fixed Qwen model handles screenshots and reasoning;
text-only GPT-OSS is excluded and never used as an implicit fallback.
"""
# Encode private local screenshots directly into the multimodal request.
import base64
# Share prompt construction, schema, image limits, and validation with Gemini.
from models.base import DECISION_SCHEMA, decision_schema, decision_prompt, parse_decision, screenshot_files
# Keep website instructions lower priority than the real user's browsing policy.
from agent.prompts import AGENT_RULES
# Distinguish setup failures from recoverable navigation/model timing problems.
from domain.errors import ProviderConfigurationError
# Keep the exact user-accessible image-capable model fixed.
GROQ_MODEL = "qwen/qwen3.8-27b"


# Reuse a single lazy OpenAI-compatible client for this selected provider.
class GroqProvider:
    """Produce grounded decisions from text and images using only Groq Qwen."""

    # Allow SDK-shaped fake clients for isolated transport tests.
    def __init__(self, api_key: str, client=None):
        """Retain a runtime key and optional client; initialization performs no network work."""
        # Keep credentials outside persisted state and user-visible diagnostics.
        self._api_key = api_key
        # Initialize a real client only when the first decision is needed.
        self._client = client

    # Use Qwen for both visual understanding and the resulting action.
    def decide(self, task, observation, history):
        """Return a strict validated action; propagate request failures to bounded recovery."""
        # Create one bounded-timeout client only when Groq is selected.
        if self._client is None:
            # Avoid importing an unused provider SDK at application startup.
            from openai import OpenAI
            # Disable implicit retries so the workflow owns attempt accounting.
            self._client = OpenAI(api_key=self._api_key, base_url="https://api.groq.com/openai/v1", timeout=45, max_retries=0)
        # Put the same shared navigation prompt into multimodal content.
        content = [{"type": "text", "text": decision_prompt(task, observation, history)}]
        # Respect Qwen's image limit without discarding stored extraction evidence.
        for path in screenshot_files(observation):
            # Convert immutable screenshots to data URIs without public image hosting.
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            # Attach a true image part rather than a textual screenshot reference.
            content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + encoded}})
        # Use strict JSON responses; LangGraph executes their validated action locally.
        try:
            # Only the selected Qwen model receives both screenshots and task context.
            response = self._client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "system", "content": AGENT_RULES}, {"role": "user", "content": content}], temperature=0, response_format={"type": "json_schema", "json_schema": {"name": "browser_decision", "strict": True, "schema": decision_schema(task, observation)}})
        # Do not repeatedly spend requests on invalid credentials or an unavailable model.
        except Exception as exc:
            # OpenAI-compatible SDK errors expose the HTTP status explicitly.
            status = getattr(exc, "status_code", None)
            # Treat access/schema/model failures as concrete setup blockers.
            if status in {400, 401, 403, 404}:
                # Preserve safe provider/model context without raw request bodies.
                raise ProviderConfigurationError("Groq", GROQ_MODEL, status) from exc
            # Bounded shared recovery handles transient timing and quota responses.
            raise
        # Never replace a valid action or blocker with a fabricated finish.
        return parse_decision(response.choices[0].message.content or "{}")
