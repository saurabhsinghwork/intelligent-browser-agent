"""Check task-relevant targeting context on large real-shaped navigation menus."""
# Decode the bounded model prompt without making a provider request.
import json
# Supply a complete observation independently of prompt truncation.
from domain.models import BrowserObservation
# Exercise the actual shared Gemini/Groq prompt builder.
from models.base import decision_prompt

# A subject link beyond the first 35 controls must be available for grounded input.
def test_subject_target_survives_large_navigation():
    """Retain actual operator identity without changing complete source observations."""
    # Reproduce a large page with unrelated visible menu controls first.
    elements = [{"id_label":str(index),"text":"Menu option","in_view":True} for index in range(350)]
    # Place the intended actual subject beyond the old first-controls cutoff.
    elements.append({"id_label":"actual-operators","text":"Python Operators","href":"https://example.com/python/operators","in_view":True})
    # Keep the complete observation separate from navigation context.
    observation = BrowserObservation("https://example.com", elements=elements)
    # Build the production prompt for the user's subject request.
    prompt = decision_prompt("all python operator details from that site", observation, [])
    # Decode the clearly separated context payload.
    context = json.loads(prompt.split("\n",1)[1])
    # The model must receive the exact actual element ID instead of inventing one.
    assert any(item["id_label"] == "actual-operators" for item in context["elements"])
    # Navigation compaction must never discard full retained observations.
    assert len(observation.elements) == 351
