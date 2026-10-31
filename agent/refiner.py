"""Intelligent task understanding and query refinement.

Analyzes raw natural-language user instructions, disambiguates target domain,
entity, counts, constraints, detail levels, and strategy, and constructs a
hallucination-free execution contract.
"""
# Preserve structured refinement data as typed records.
from dataclasses import asdict, dataclass, field
# Extract semantic entities, numbers, and constraints via robust regex.
import re
# Normalize URLs and query parameters safely.
from urllib.parse import quote_plus, urlparse


# Describe a fully understood and refined task contract.
@dataclass(frozen=True)
class TaskRefinement:
    """Store the structured interpretation of an ambiguous user task."""
    # Retain original instruction verbatim for auditability.
    original_prompt: str
    # Understood domain or target website.
    domain: str = ""
    # Resolved direct starting URL if query parameters are identifiable.
    direct_url: str = ""
    # Logical entity type (e.g., job, product, article).
    entity: str = "record"
    # Target record count.
    required_count: int | None = None
    # Concrete search and filter constraints.
    constraints: dict[str, str] = field(default_factory=dict)
    # Detail depth: full (detail pane/page) vs summary (cards).
    detail_level: str = "summary"
    # Specialized domain strategy identifier.
    strategy: str = "standard"
    # Disambiguated human-readable objective.
    clarified_objective: str = ""
    # Concrete sequential steps to achieve the goal without hallucination.
    execution_steps: list[str] = field(default_factory=list)


# Refine ambiguous user queries into structured contracts.
def refine_task(prompt, selected_site=None):
    """Understand user intent, disambiguate constraints, and select execution strategy."""
    # Normalize input text.
    raw = str(prompt or "").strip()
    # Lowercase text for matching.
    lowered = raw.lower()
    # Extract candidate website or domain mentions.
    domain = ""
    # Check for prominent platform mentions in text or selected site.
    if "linkedin" in lowered or (selected_site and "linkedin" in selected_site.lower()):
        # Set LinkedIn as target domain.
        domain = "linkedin.com"
    # Check for Amazon.
    elif "amazon" in lowered or (selected_site and "amazon" in selected_site.lower()):
        # Set Amazon as target domain.
        domain = "amazon.com"
    # Check for W3Schools.
    elif "w3schools" in lowered or (selected_site and "w3schools" in selected_site.lower()):
        # Set W3Schools as target domain.
        domain = "w3schools.com"
    # Fallback to selected site hostname if available.
    elif selected_site:
        # Extract hostname from selected site URL.
        domain = urlparse(selected_site if "://" in selected_site else "https://" + selected_site).hostname or ""
    # Extract explicit count.
    count_match = re.search(r"\b(?:collect|fetch|find|get|scrape|bring|extract)?\s*(?:at\s+least\s+)?(\d+)\b", lowered)
    # Parse integer count or default to None.
    count = int(count_match.group(1)) if count_match else None
    # Determine entity type.
    entity = "record"
    # Detect job entities.
    if re.search(r"\b(job|jobs|role|roles|position|positions|opening|openings|career|careers)\b", lowered) or "linkedin" in domain:
        # Classify as job entity.
        entity = "job"
    # Detect product entities.
    elif re.search(r"\b(product|products|item|items|goods|price|prices|laptop|laptops|phone|phones|shoes)\b", lowered) or "amazon" in domain:
        # Classify as product entity.
        entity = "product"
    # Detect article/tutorial entities.
    elif re.search(r"\b(article|articles|tutorial|tutorials|post|posts|guide|guides|chapter|chapters)\b", lowered):
        # Classify as article entity.
        entity = "article"
    # Determine detail level: full vs summary.
    full_detail = bool(
        # Check for phrases requesting complete detail or explicitly rejecting card-only summaries.
        re.search(
            r"\b(complete|full|entire|detailed|all)\s+(?:job\s+)?details?\b|\bnot\s+(?:only|just)\s+(?:the\s+)?(?:job\s+)?cards?\b|\bjob\s+details\b|\bdescription\b",
            lowered
        )
    )
    # Extract location constraint if present.
    constraints = {}
    # Find phrases like "in pune", "near pune", "at pune".
    loc_match = re.search(r"\b(?:in|near|at)\s+([a-z][a-z .'-]{1,40}?)(?:\s+(?:from|on|with|having|using|under|over|complete|full|detail|not)\b|$)", lowered)
    # Validate matched location phrase.
    if loc_match:
        # Clean location value.
        loc_val = loc_match.group(1).strip(" ,.'")
        # Reject non-location noise words.
        if loc_val not in {"linkedin", "detail", "details", "full", "complete", "left panel", "job cards"}:
            # Store extracted location.
            constraints["location"] = loc_val
    # Extract subject or keyword constraint.
    keyword = ""
    # Check for keyword patterns like "10 python" or "python jobs" or "about python".
    kw_match = re.search(r"\b(?:collect|find|get)?\s*(?:\d+\s+)?([a-z0-9+#.-]+)\s+(?:in|near|at|jobs?|roles?|products?|from)\b", lowered)
    # Validate keyword candidate.
    if kw_match:
        # Extract candidate string.
        candidate_kw = kw_match.group(1).strip()
        # Reject generic stopwords.
        if candidate_kw not in {"collect", "fetch", "find", "get", "scrape", "the", "some", "any", "jobs", "job", "in", "from", "on", "all"}:
            # Set extracted keyword.
            keyword = candidate_kw
    # Fallback to checking specific popular technologies or subjects.
    if not keyword:
        # Look for programming languages and common technical subjects.
        for tech in ("python", "javascript", "typescript", "java", "golang", "rust", "react", "c++", "data science", "machine learning", "devops", "sql"):
            # Check presence in prompt.
            if tech in lowered:
                # Assign identified technology.
                keyword = tech
                # Stop search.
                break
    # Assign keyword to constraints if found.
    if keyword:
        # Store keyword constraint.
        constraints["keyword"] = keyword
    # Select execution strategy.
    strategy = "standard"
    # Select LinkedIn strategy for linkedin.com or job searches on LinkedIn.
    if "linkedin" in domain or "linkedin" in lowered:
        # Set strategy to linkedin.
        strategy = "linkedin"
    # Build direct search URL when possible.
    direct_url = ""
    # Generate LinkedIn job search URL if relevant constraints are present.
    if strategy == "linkedin" and ("keyword" in constraints or "location" in constraints):
        # Format LinkedIn jobs search URL.
        kw_param = quote_plus(constraints.get("keyword", ""))
        # Format location parameter.
        loc_param = quote_plus(constraints.get("location", ""))
        # Assemble direct URL.
        direct_url = f"https://www.linkedin.com/jobs/search?keywords={kw_param}&location={loc_param}"
    # Construct disambiguated objective string.
    count_str = f"{count} " if count else ""
    # Construct detail description.
    detail_str = "complete details (title, company, location, full job description)" if full_detail else "summary cards"
    # Format clarified objective.
    clarified = f"Collect {count_str}{constraints.get('keyword', '').title()} {entity}s in {constraints.get('location', '').title()} with {detail_str} from {domain or 'target website'}."
    # Build step-by-step hallucination-free execution plan.
    steps = []
    # Step 1: Navigation.
    if direct_url:
        # Plan direct navigation.
        steps.append(f"Navigate directly to {direct_url} to access pre-filtered {entity} search results.")
    # Fallback navigation.
    else:
        # Plan search on landing page.
        steps.append(f"Navigate to {domain or selected_site} and apply filters: {constraints}.")
    # Step 2: Master-Detail detection.
    if strategy == "linkedin" or full_detail:
        # Describe dual-pane handling.
        steps.append("Identify the dual-pane layout: Master listing panel (left) containing cards and Detail panel (right) displaying rich entity information.")
        # Describe iterative traversal.
        steps.append(f"Iteratively select each of the first {count or 10} cards: physically glide visual cursor to card, click to activate, wait for detail pane to update.")
        # Describe disclosure handling.
        steps.append("Expand disclosure controls ('Show more', 'See more', 'Read more') within detail pane to expose the complete description.")
        # Describe extraction.
        steps.append("Extract title, company/organization, location, and the entire job description text; verify detail completeness.")
        # Describe scrolling.
        steps.append("When visible cards in master panel are exhausted, scroll master panel with 1-line overlap (viewport - 32px) until the required count is satisfied.")
    # Standard page traversal.
    else:
        # Describe standard extraction.
        steps.append(f"Collect qualifying {entity} records up to {count or 'all available'} items with measured viewport scrolling.")
    # Final step: Verification and assembly.
    steps.append(f"Verify that exactly {count or 'all'} unique records meeting constraints {constraints} are gathered without hallucination and assemble output.")
    # Construct typed refinement.
    refinement = TaskRefinement(
        original_prompt=raw,
        domain=domain,
        direct_url=direct_url,
        entity=entity,
        required_count=count,
        constraints=constraints,
        detail_level="full" if full_detail else "summary",
        strategy=strategy,
        clarified_objective=clarified,
        execution_steps=steps,
    )
    # Return refinement as dict.
    return asdict(refinement)
