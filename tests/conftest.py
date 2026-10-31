"""Workspace-local test fixtures compatible with restricted Windows execution.

The ordinary pytest temporary-root fixture can create ACLs inaccessible to the
sandbox token. These fixtures create only owned test directories with inherited
workspace permissions and do not touch genuine browser-session profiles.
"""
# Resolve the explicit test-artifact boundary.
from pathlib import Path
# Give every test a distinct directory without deleting another test's artifacts.
from uuid import uuid4
# Provide fixtures through the standard test runner.
import pytest


# Override only the per-test directory fixture, not application session behavior.
@pytest.fixture
def tmp_path():
    """Return a unique workspace-owned test directory with inherited permissions."""
    # Keep test files out of genuine saved browser profiles.
    root = Path(__file__).resolve().parents[1] / "data" / "test_artifacts"
    # Resolve the actual final directory before creating it.
    target = root / uuid4().hex
    # Default inherited permissions avoid restrictive explicit temporary-directory ACLs.
    target.mkdir(parents=True, exist_ok=True)
    # Retain artifacts for reproducible debugging without recursive cleanup races.
    return target
