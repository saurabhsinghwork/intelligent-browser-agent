"""Unit tests for run configuration validation."""
# Import pytest and the configuration contract.
import pytest
from config.settings import RunConfiguration
# Confirm valid mutually exclusive selections are accepted.
def test_valid_configuration():
    # Arrange a supported provider, method, visibility and key.
    config = RunConfiguration("gemini", "browser_use", True, "test-key")
    # Act and assert that validation succeeds without a return value.
    assert config.validate() is None
# Reject missing credentials.
def test_missing_key_is_rejected():
    # Arrange a configuration without a runtime credential.
    config = RunConfiguration("groq", "playwright_cli", False, " ")
    # Assert validation reports the missing key.
    with pytest.raises(ValueError, match="API key"):
        config.validate()
# Reject unlisted browser methods rather than silently selecting another method.
def test_extra_browser_method_is_rejected():
    # Arrange a method not listed in the approved three options.
    config = RunConfiguration("gemini", "browser_use_cli", False, "test-key")
    # Assert the method cannot be selected.
    with pytest.raises(ValueError, match="browser method"):
        config.validate()
