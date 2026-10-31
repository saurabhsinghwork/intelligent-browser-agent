"""Ground link-only model replies without mutating ordinary navigation requests."""
# Construct current observed link batches without browser access.
from domain.models import BrowserObservation
# Exercise the production provider-neutral response schema.
from models.base import decision_schema, DECISION_SCHEMA

# Dedicated relevance review must never invent destinations or ordinary actions.
def test_review_schema_is_grounded():
    """Allow only queue_links and observed URLs while retaining the base schema."""
    # Supply one real destination twice to verify stable deduplication.
    observation = BrowserObservation("https://example.com", links=[{"url":"https://example.com/a"},{"url":"https://example.com/a"}])
    # Build exactly the schema used in both provider requests.
    schema = decision_schema("LINK REVIEW ONLY: choose relevant links", observation)
    # This stage cannot return finish and prematurely discard its candidate batch.
    assert schema["properties"]["kind"]["enum"] == ["queue_links"]
    # Responses cannot select a destination absent from this real batch.
    assert schema["properties"]["links"]["items"]["enum"] == ["https://example.com/a"]
    # Request-specific restrictions cannot contaminate ordinary navigation.
    assert "finish" in DECISION_SCHEMA["properties"]["kind"]["enum"]
    # Normal decisions retain the shared existing schema.
    assert decision_schema("Read this page", observation) is DECISION_SCHEMA

# An empty real batch must not produce a schema with an invalid empty enum.
def test_empty_review_schema():
    """Permit an empty selection without allowing invented URLs."""
    # No discovered link can be selected in this request.
    schema = decision_schema("LINK REVIEW ONLY", BrowserObservation("https://example.com"))
    # The only valid link array is empty.
    assert schema["properties"]["links"]["maxItems"] == 0
