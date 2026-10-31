"""Check multimodal requests, fixed model IDs, and no-fallback behavior offline.

SDK-shaped clients capture actual transport payloads. These tests prove image
construction and response parsing, not account access or live model performance.
"""
# Construct SDK-shaped deterministic responses.
from types import SimpleNamespace
# Decode image payloads for exact transport assertions.
import base64
# Verify genuine error propagation without a hidden model substitution.
import pytest
# Supply current screenshot references and complete raw source.
from domain.models import BrowserObservation
# Exercise both actual request builders and fixed configured model IDs.
from models.gemini_provider import GeminiProvider, GEMINI_MODEL
from models.groq_provider import GroqProvider, GROQ_MODEL


# Both selected transports must receive actual screenshots and preserve action decisions.
def test_fixed_models_receive_images(tmp_path):
    """Send PNG bytes to Gemini and image data URIs to Groq Qwen, never GPT-OSS."""
    # Create an owned image marker; request construction uses its actual bytes.
    image = tmp_path / "viewport.png"
    # A valid one-pixel PNG keeps this request-shape test independent of a browser.
    image.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l4kAAAAASUVORK5CYII="))
    # Keep captured requests separate for each provider.
    calls = {"gemini": [], "groq": []}
    # Return one valid next action without a final answer.
    response = '{"kind":"click","target":"target","output":""}'

    # Capture the actual Gemini image/config request.
    def gemini_request(**kwargs):
        """Record transport fields and return a deterministic structured decision."""
        # Preserve the exact generated payload for assertions.
        calls["gemini"].append(kwargs)
        # A provider must not convert this action into finish.
        return SimpleNamespace(text=response)

    # Capture the actual Groq multimodal request.
    def groq_request(**kwargs):
        """Record text/image parts and return the SDK's completion response shape."""
        # Preserve the selected fixed model and constrained JSON fields.
        calls["groq"].append(kwargs)
        # Keep the SDK nesting faithful to production.
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=response))])

    # Supply real local screenshot bytes as current evidence.
    observation = BrowserObservation("https://example.com", text="Long visible source " * 20, screenshot_path=str(image))
    # Use only the injected Gemini client.
    gemini = GeminiProvider("dummy-key", SimpleNamespace(models=SimpleNamespace(generate_content=gemini_request)))
    # Use only the injected Groq client.
    groq = GroqProvider("dummy-key", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=groq_request))))
    # Both models must preserve the ordinary action.
    assert gemini.decide("Click target", observation, []).kind == "click"
    # Qwen handles the screenshot and action itself, without a Gemini handoff.
    assert groq.decide("Click target", observation, []).kind == "click"
    # Freeze exactly the accessible models agreed by the user.
    assert calls["gemini"][0]["model"] == GEMINI_MODEL == "gemini-3.5-flash-lite"
    # The Groq model must be vision-capable Qwen rather than text-only GPT-OSS.
    assert calls["groq"][0]["model"] == GROQ_MODEL == "qwen/qwen3.8-27b"
    # The Gemini request contains a binary image part, not only a textual path.
    assert calls["gemini"][0]["contents"][1].inline_data.data == image.read_bytes()
    # The Groq request contains a genuine image part.
    parts = next(message["content"] for message in calls["groq"][0]["messages"] if message["role"] == "user")
    # Read the exact encoded image supplied to the selected Qwen model.
    assert base64.b64decode(parts[1]["image_url"]["url"].split(",", 1)[1]) == image.read_bytes()
    # Strict action output remains on the selected provider.
    assert calls["groq"][0]["response_format"]["json_schema"]["strict"] is True


# An unavailable model must not silently use a different billed/unsupported model.
def test_gemini_unavailable_model_has_no_fallback():
    """A 404 propagates once and preserves the fixed model policy."""
    # Record how many actual transport attempts occur.
    calls = []

    # Simulate an account/model availability failure.
    def unavailable(**kwargs):
        """Fail the fixed model without generating a substitute response."""
        # Retain the attempted ID for an explicit assertion.
        calls.append(kwargs["model"])
        # The configured account cannot access this model.
        raise RuntimeError("404 model unavailable")
    # Inject the failing transport rather than using a real API key.
    provider = GeminiProvider("dummy", SimpleNamespace(models=SimpleNamespace(generate_content=unavailable)))
    # Require explicit configuration failure instead of silent substitution.
    with pytest.raises(RuntimeError, match="404"):
        # No alternate provider/model can resolve this call implicitly.
        provider.decide("Read source", BrowserObservation("https://example.com"), [])
    # Only the one approved model was requested.
    assert calls == ["gemini-3.5-flash-lite"]
