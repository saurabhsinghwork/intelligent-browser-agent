"""Unit tests for intelligent task understanding and query refinement."""
# Test user prompt disambiguation and structured contract compilation.
from agent.refiner import refine_task


# Test LinkedIn user prompt with explicit detail depth request.
def test_refine_linkedin_task_with_full_details():
    """Disambiguate 'collect 10 python in pune from linkedin. and i mentioned that collect the job details not the job cards'."""
    # Supply the exact user instruction.
    prompt = "collect 10 python in pune from linkedin. and i mentioned that collect the job details not the job cards in the left panel"
    # Refine instruction.
    refinement = refine_task(prompt)
    # Check domain identification.
    assert refinement["domain"] == "linkedin.com"
    # Check entity classification.
    assert refinement["entity"] == "job"
    # Check target count extraction.
    assert refinement["required_count"] == 10
    # Check constraints.
    assert refinement["constraints"]["location"].lower() == "pune"
    assert refinement["constraints"]["keyword"].lower() == "python"
    # Check detail level.
    assert refinement["detail_level"] == "full"
    # Check strategy selection.
    assert refinement["strategy"] == "linkedin"
    # Check direct URL construction.
    assert "keywords=python" in refinement["direct_url"]
    assert "location=pune" in refinement["direct_url"]
    # Check execution steps presence.
    assert len(refinement["execution_steps"]) >= 4


# Test generic product query refinement.
def test_refine_product_query():
    """Disambiguate product search queries."""
    # Supply prompt.
    prompt = "find 5 laptops under 50000 on amazon"
    # Refine instruction.
    refinement = refine_task(prompt)
    # Verify domain.
    assert refinement["domain"] == "amazon.com"
    # Verify entity.
    assert refinement["entity"] == "product"
    # Verify count.
    assert refinement["required_count"] == 5
