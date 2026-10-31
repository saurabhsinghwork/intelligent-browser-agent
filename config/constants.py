"""Central identifiers and fixed limits. This file owns names and defaults, not runtime secrets."""
# Define the exact provider identifiers accepted by the application.
MODEL_PROVIDERS = ("gemini", "groq")
# Define the exact three browser execution methods from the specification.
BROWSER_METHODS = ("playwright_mcp", "playwright_cli", "browser_use")
# Bound retries for one failed decision as required by the specification.
MAX_ATTEMPTS_PER_DECISION = 5
# Keep website discovery constrained to the requested number of candidates.
MIN_WEBSITE_CANDIDATES = 3
# Never offer more than five actual distinct search results.
MAX_WEBSITE_CANDIDATES = 5
