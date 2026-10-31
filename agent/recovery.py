"""Bounded recovery helpers. Attempts count against the same decision and reset only after verified progress."""
# Import the documented retry limit.
from config.constants import MAX_ATTEMPTS_PER_DECISION
# Return the next attempt count or raise after the fifth failed attempt.
def next_attempt(current: int) -> int:
    """Increment the retry counter and refuse a sixth attempt for the same failed decision."""
    # Compute the next attempt number.
    attempt = current + 1
    # Stop recovery when the documented limit has been exhausted.
    if attempt > MAX_ATTEMPTS_PER_DECISION:
        # A helper caller must not start a sixth failed-problem retry.
        raise RuntimeError("Five attempts exhausted for this decision.")
    # Return the accepted attempt number.
    return attempt
