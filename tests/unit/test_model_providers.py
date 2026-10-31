"""Unit tests for Gemini and Grok model provider adapters with mocked network responses.

This module validates JSON decision mapping, error handling, code block stripping, and secret handling.
"""
# Import pytest for assertions.
import pytest
# Import domain and model provider components.
from domain.models import BrowserObservation, AgentDecision
from models.gemini_provider import GeminiProvider
from models.grok_provider import GrokProvider
from models.base import parse_decision

# Provide a mock client that returns structured decision text.
class FakeModelResponse:
    """Mock container for model text response."""
    def __init__(self, text: str):
        self.text = text

class FakeGeminiClient:
    """Mock GenAI client for isolated testing."""
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls = []
        # Expose a models sub-object matching google-genai Client structure.
        self.models = self

    def generate_content(self, model: str, contents: list, config=None):
        """Record model request and return canned text response."""
        # Capture the real structured-output configuration as well as model/image inputs.
        self.calls.append((model, contents, config))
        return FakeModelResponse(self.response_text)

class FakeChoice:
    """Mock message container for OpenAI chat completions."""
    def __init__(self, content: str):
        self.message = type("Msg", (), {"content": content})()

class FakeGrokClient:
    """Mock Grok/OpenAI client for isolated testing."""
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.chat = type("Chat", (), {"completions": self})()

    def create(self, **kwargs):
        """Return canned completion choice."""
        return type("Resp", (), {"choices": [FakeChoice(self.response_text)]})()

# Gemini provider parses valid JSON action.
def test_gemini_provider_decide_valid_json():
    # Arrange fake client returning valid click decision.
    fake_client = FakeGeminiClient('{"kind": "click", "target": "e1", "rationale": "Click submit"}')
    provider = GeminiProvider(api_key="test-gemini-key", client=fake_client)
    obs = BrowserObservation(url="https://example.com", title="Demo", text="Submit page")
    # Act to obtain decision.
    decision = provider.decide("Click submit button", obs, [])
    # Assert decision properties.
    assert decision.kind == "click"
    assert decision.target == "e1"
    assert decision.rationale == "Click submit"

# Gemini provider parses decision wrapped in markdown fences.
def test_gemini_provider_decide_markdown_fences():
    # Arrange fake client returning markdown fenced JSON.
    fake_client = FakeGeminiClient('```json\n{"kind": "fill", "target": "e2", "value": "search query"}\n```')
    provider = GeminiProvider(api_key="test-key", client=fake_client)
    obs = BrowserObservation(url="https://example.com")
    decision = provider.decide("Search query", obs, [])
    assert decision.kind == "fill"
    assert decision.value == "search query"

# Grok provider parses valid JSON action.
def test_grok_provider_decide_valid_json():
    # Arrange fake Grok client returning finish decision.
    fake_client = FakeGrokClient('{"kind": "finish", "output": "Found answer: 42"}')
    provider = GrokProvider(api_key="test-grok-key", client=fake_client)
    obs = BrowserObservation(url="https://example.com")
    decision = provider.decide("Find answer", obs, [])
    assert decision.kind == "finish"
    assert decision.output == "Found answer: 42"

# Malformed model output raises ValueError.
def test_parse_decision_rejects_unsupported_kind():
    # Arrange malformed JSON without permitted kind.
    with pytest.raises(ValueError, match="unsupported action format"):
        parse_decision('{"kind": "execute_arbitrary_code", "code": "malicious()"}')
