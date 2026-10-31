"""Faithful result presentation helpers independent of model-generated prose.

Original extracted text is never stripped, auto-converted from JSON, summarized,
or hidden when a task is partial. Structured Markdown is produced by EvidenceStore.
"""


# Keep raw source output unchanged for legacy callers.
def format_output_presentation(content):
    """Return captured content exactly; choosing a visual format must be explicit."""
    # Preserve whitespace and literal JSON rather than reinterpreting source text.
    return content


# Label incomplete outcomes separately while preserving their available source content.
def render_output(output, blocker="", verified=False):
    """Return exact output plus a separate explanatory notice for partial/unverified runs."""
    # Preserve both limitation and already collected information.
    if blocker:
        # Never discard useful source evidence merely because a later page was blocked.
        return "Unable to complete the task: " + blocker + ("\n\n" + output if output else "")
    # Clearly distinguish unverified data from complete success.
    if not verified:
        # The user can inspect partial evidence without a false success label.
        return "The task result has not been verified yet." + ("\n\n" + output if output else "")
    # Verified output is already assembled deterministically from captured evidence.
    return output or "The task completed, but no result content was produced."
