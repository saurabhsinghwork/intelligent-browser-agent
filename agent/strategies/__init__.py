"""Domain and website execution strategies.

Specialized domain strategies define generalized patterns (e.g. master-detail
split panes) without binding to fragile single-account CSS classes.
"""
# Export available strategies.
from agent.strategies.linkedin import LinkedInStrategy

__all__ = ["LinkedInStrategy"]
