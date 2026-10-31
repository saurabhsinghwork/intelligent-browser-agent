"""Unit tests for generalized LinkedIn master-detail strategy."""
# Types for mock adapter and observation records.
from types import SimpleNamespace
# Test LinkedInStrategy matches and traversal mechanics.
from agent.strategies.linkedin import LinkedInStrategy


# Verify strategy matching on goal and URL.
def test_linkedin_strategy_matches():
    """Verify strategy matching for explicit goals, objectives, and URLs."""
    # Match on explicit strategy property.
    assert LinkedInStrategy.matches({"strategy": "linkedin"}) is True
    # Match on objective mentioning linkedin.
    assert LinkedInStrategy.matches({"objective": "Find jobs on LinkedIn"}) is True
    # Match on URL.
    assert LinkedInStrategy.matches({}, "https://www.linkedin.com/jobs/search") is True
    # Do not match unrelated site.
    assert LinkedInStrategy.matches({"objective": "Learn python on w3schools"}, "https://w3schools.com") is False


# Verify master-detail extraction flow on mock browser adapter.
def test_linkedin_strategy_collect_jobs():
    """Verify card iteration, detail expansion, and clean record assembly."""
    # Mock cards discovery payload.
    discovery_payload = {
        "master_found": True,
        "cards_count": 2,
        "cards": [
            {"id_label": "iba-job-card-0", "index": 0, "title": "Python Engineer", "company": "Tech Corp", "in_view": True},
            {"id_label": "iba-job-card-1", "index": 1, "title": "Senior Python Dev", "company": "Data Labs", "in_view": True},
        ]
    }
    # Mock detail extraction payload.
    detail_payload = {
        "title": "Python Engineer",
        "company": "Tech Corp",
        "location": "Pune, India",
        "description": "We are seeking a Python Engineer to develop scalable backend microservices and APIs.",
        "expanded": True,
        "length": 85
    }
    # Track executed decisions.
    executed_decisions = []
    # Create fake adapter.
    class FakeAdapter:
        # Check cancellation mock.
        def check_cancelled(self):
            pass
        # Evaluate mock returning structured discovery or detail.
        def _evaluate(self, script):
            if "uniqueCards" in script or "masterContainer" in script:
                return discovery_payload
            if "two-pane-serp-page__detail-view" in script or "jobs-search__job-details" in script or "detailContainer" in script:
                return detail_payload
            return {"scrolled": True}
        # Observe mock.
        def observe(self):
            return SimpleNamespace(screenshot_path="data/test.png", observation_id="fake-obs-1")
        # Execute mock recording clicks.
        def execute(self, decision):
            executed_decisions.append(decision)
            return {"success": True}
        # Probe mock.
        def probe(self):
            return {"url": "https://www.linkedin.com/jobs/search?keywords=python&location=pune"}
    # Run strategy collection.
    report = LinkedInStrategy.collect_jobs(FakeAdapter(), {"required_count": 1, "constraints": {"location": "pune"}})
    # Assertions on collected report.
    assert report["task_complete"] is True
    assert len(report["blocks"]) >= 1
    # Verify detail_complete flag.
    assert report["blocks"][0]["detail_complete"] is True
    # Verify extracted description.
    assert "Job Description:" in report["blocks"][0]["text"]
    assert "Tech Corp" in report["blocks"][0]["text"]


# Verify that existing store records are resumed and not duplicated.
def test_linkedin_strategy_resumes_existing_store_and_sync():
    """Verify that prior progress in store is loaded and traversal completes remaining count."""
    class MockStore:
        def __init__(self):
            self._blocks = [{
                "key": "pre-existing-1",
                "title": "Python Engineer",
                "company": "Tech Corp",
                "location": "Pune",
                "text": "Job Description: Pre-existing description",
                "detail_complete": True
            }]
        def blocks(self):
            return list(self._blocks)
        def add(self, data, scope, offset, count):
            self._blocks.extend(data.get("blocks", []))

    discovery_payload = {
        "cards_count": 2,
        "cards": [
            {"id_label": "iba-job-card-0", "index": 0, "title": "Python Engineer", "company": "Tech Corp", "in_view": True},
            {"id_label": "iba-job-card-1", "index": 1, "title": "Senior Python Dev", "company": "Data Labs", "in_view": True},
        ]
    }
    detail_payload_2 = {
        "title": "Senior Python Dev",
        "company": "Data Labs",
        "location": "Pune, India",
        "description": "We are looking for Senior Python Dev with deep Django, FastAPI, and AWS experience.",
        "expanded": True,
        "length": 88
    }

    class FakeAdapter:
        def check_cancelled(self):
            pass
        def _evaluate(self, script):
            if "uniqueCards" in script:
                return discovery_payload
            if "Senior Python Dev" in script or "iba-job-card-1" in script:
                return detail_payload_2
            return detail_payload_2
        def observe(self):
            return SimpleNamespace(screenshot_path="data/test2.png", observation_id="fake-obs-2")
        def execute(self, decision):
            return {"success": True}
        def probe(self):
            return {"url": "https://www.linkedin.com/jobs/search?keywords=python&location=pune"}

    store = MockStore()
    goal = {"required_count": 2, "constraints": {"location": "pune"}}
    report = LinkedInStrategy.collect_jobs(FakeAdapter(), goal, store=store)

    assert report["complete"] is True
    assert len(report["blocks"]) == 2
    titles = [b["title"] for b in report["blocks"]]
    assert "Python Engineer" in titles
    assert "Senior Python Dev" in titles


# Verify that if store already satisfies goal count, strategy returns immediately without browser calls.
def test_linkedin_strategy_fast_path_when_store_already_satisfied():
    """Verify that no clicks or evaluations occur when target count is already met in store."""
    class MockStore:
        def blocks(self):
            return [
                {"key": "job-1", "title": "Python Dev", "company": "A", "location": "Pune", "text": "desc 1", "detail_complete": True},
                {"key": "job-2", "title": "Python Lead", "company": "B", "location": "Pune", "text": "desc 2", "detail_complete": True},
            ]

    class StrictAdapter:
        def check_cancelled(self):
            pass
        def probe(self):
            return {"url": "https://www.linkedin.com/jobs/search?keywords=python"}
        def _evaluate(self, script):
            raise AssertionError("Should not evaluate scripts when goal is already met in store")
        def observe(self):
            raise AssertionError("Should not observe when goal is already met in store")

    goal = {"required_count": 2, "constraints": {"location": "pune"}}
    report = LinkedInStrategy.collect_jobs(StrictAdapter(), goal, store=MockStore())
    assert report["complete"] is True
    assert report["task_complete"] is True
    assert len(report["blocks"]) == 2


# Verify that batch collection properly parses and stores blocks including entity_url.
def test_linkedin_strategy_batch_collection_success():
    """Verify that batch evaluation results assemble complete job blocks properly with job_url."""
    batch_payload = {
        "batch": [
            {
                "title": "Python Engineer",
                "company": "FastTech",
                "location": "Bengaluru",
                "description": "Building microservices in Python with FastAPI and Docker.",
                "url": "https://www.linkedin.com/jobs/view/12345"
            },
            {
                "title": "Backend Python Developer",
                "company": "CloudCorp",
                "location": "Bengaluru",
                "description": "High performance async data pipelines with Python and Redis.",
                "url": "https://www.linkedin.com/jobs/view/67890"
            }
        ]
    }

    class MockAdapter:
        def check_cancelled(self):
            pass
        def _evaluate(self, script):
            if "batch" in script:
                return batch_payload
            return {}
        def observe(self):
            return SimpleNamespace(screenshot_path="data/test_batch.png", observation_id="fake-obs-batch")
        def probe(self):
            return {"url": "https://www.linkedin.com/jobs/search?keywords=python&location=bengaluru"}

    goal = {"required_count": 2, "constraints": {"location": "bengaluru", "keyword": "python"}}
    report = LinkedInStrategy.collect_jobs(MockAdapter(), goal)
    assert report["complete"] is True
    assert len(report["blocks"]) == 2
    assert report["blocks"][0]["title"] == "Python Engineer"
    assert report["blocks"][0]["entity_url"] == "https://www.linkedin.com/jobs/view/12345"
    assert report["blocks"][1]["title"] == "Backend Python Developer"



