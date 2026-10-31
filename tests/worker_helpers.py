"""Spawn-safe deterministic model factories for real browser/worker diagnostics.

These providers never make API requests. They isolate worker lifecycle and crawl
behavior; separate multimodal tests and future real-key tests validate providers.
"""
# Simulate a slow in-flight model call for bounded Stop verification.
import time
# Return the same normalized action records as real provider adapters.
from domain.models import AgentDecision
# Provide exact source quotations for the independent semantic completion audit.
import json


# Choose finite source collection using explicit measured progress supplied by the agent.
class ControlledProvider:
    """Drive two linked local chapters while leaving extraction and verification real."""

    # Keep the exact normal provider interface for dependency injection.
    def decide(self, task, observation, history):
        """Select actual relevant links and request capture before proposing completion."""
        # A completion audit must cite source rather than return an unsupported confidence flag.
        if "COMPLETION AUDIT" in task:
            # Both requested chapters must be represented by actual exact evidence.
            return AgentDecision(kind="finish", expected="objective_met", value=json.dumps(["Original first chapter: ₹1,299.00.", "Original second chapter: unchanged wording."]))
        # Relevance review must classify only URLs in the supplied batch.
        if "LINK REVIEW ONLY" in task:
            # Preserve the actual next-chapter order without inventing URLs.
            return AgentDecision(kind="queue_links", links=[item["url"] for item in observation.links if item["text"] == "Next chapter"])
        # The controller exposes actual measured collection state, not model assertions.
        if '"current_page_collected": true' in task:
            # Final source output remains owned by EvidenceStore.
            return AgentDecision(kind="finish")
        # Collect actual rendered source from the requested chapter region.
        return AgentDecision(kind="collect", target="main")


# Simulate a provider that cannot immediately return from an in-flight request.
class SlowProvider:
    """Block a model call so Stop must use the worker's cancellation boundary."""

    # No actual paid API is contacted in this diagnostic.
    def decide(self, task, observation, history):
        """Delay beyond the Stop cleanup deadline, then return an ordinary proposal."""
        # This deliberate blocking call tests process isolation, not browser speed.
        time.sleep(20)
        # A supervisor must stop the run before this delayed result can act.
        return AgentDecision(kind="finish")


# Provide a top-level picklable factory for Windows spawn.
def controlled_provider(provider_name, api_key):
    """Construct the deterministic test provider; ignore the nonsecret marker key."""
    # Do not initialize or silently fall back to any real model.
    return ControlledProvider()


# Supply a separate spawn-safe factory for the blocked-call cancellation scenario.
def slow_provider(provider_name, api_key):
    """Return a deliberate slow fake, keeping the browser and worker otherwise real."""
    # The supervisor must own and terminate this exact process.
    return SlowProvider()

# Reproduce a spare target field emitted by the real model during batch review.
class NoisyReviewProvider(ControlledProvider):
    """Keep actual chapter decisions while adding the observed irrelevant target field."""
    # Use the same production model interface.
    def decide(self,task,observation,history):
        """Return the observed batch-response shape without changing selected destinations."""
        # Reuse the deterministic subject/collection/audit behavior.
        decision=super().decide(task,observation,history)
        # Only link-review batches receive the spare page-rejection target.
        if "LINK REVIEW ONLY" in task:
            # Keep the exact real link selection and reproduce the formerly conflicting field.
            return AgentDecision(kind="queue_links",target="skip_current",links=decision.links,rationale="Review this actual batch")
        # All other task stages retain the original controlled behavior.
        return decision

# Keep the regression provider spawn-safe on Windows.
def noisy_review_provider(provider_name,api_key):
    """Construct the explicit live-response-shape regression fake."""
    # No paid service or runtime credential is used by this diagnostic.
    return NoisyReviewProvider()
