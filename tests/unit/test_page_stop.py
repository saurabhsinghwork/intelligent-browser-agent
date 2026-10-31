"""Protect explicit page stopping without changing broader website exploration."""
# Parametrize actual user wording and broader-task counterexamples.
import pytest
# Exercise the real page-boundary decision helper.
from agent.nodes import _page_only_task


# Explicit page boundaries must be respected before considering a website link frontier.
@pytest.mark.parametrize("task", ["all python operators detail from that page", "get all details on this page", "extract from the current page", "this page only"])
def test_explicit_page_boundary(task):
    """Recognize that the user requested one page rather than a website crawl."""
    # Preserve the stated page boundary even when the user asks for all information.
    assert _page_only_task(task)


# The fix must not disable previously approved broad site and chapter tasks.
@pytest.mark.parametrize("task", ["retrieve the complete Python tutorial and its chapters", "bring the client details from the website", "search the website for all relevant products"])
def test_website_scope_is_unchanged(task):
    """Retain automatic relevant-link behavior for instructions without a single-page boundary."""
    # Do not impose a page-only stop on broader website tasks.
    assert not _page_only_task(task)
