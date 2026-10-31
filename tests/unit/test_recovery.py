"""Unit tests for bounded recovery."""
# Import pytest and retry counter.
import pytest
from agent.recovery import next_attempt
# Allow exactly the first five attempts.
def test_five_attempts_allowed():
    # Count each attempt sequentially.
    attempts = 0
    for _ in range(5):
        attempts = next_attempt(attempts)
    # Assert the final accepted count is five.
    assert attempts == 5
# Reject a sixth attempt.
def test_sixth_attempt_rejected():
    # Assert the counter does not allow another attempt after five failures.
    with pytest.raises(RuntimeError, match="Five attempts"):
        next_attempt(5)
