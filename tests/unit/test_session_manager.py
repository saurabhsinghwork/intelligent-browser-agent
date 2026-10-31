"""Unit tests for browser session manager, covering isolation, existence checks, and clearing."""
# Import pytest and temporary path fixture.
import pytest
from pathlib import Path
# Import session manager helpers.
from browser.session_manager import (
    session_path,
    ensure_session_dir,
    has_session,
    clear_session,
    clear_all_sessions,
)

# Sessions for different websites must have isolated paths.
def test_session_path_isolation(tmp_path: Path):
    # Compute path for site A.
    path_a = session_path("https://a.example", "browser_use", root=tmp_path)
    # Compute path for site B.
    path_b = session_path("https://b.example", "browser_use", root=tmp_path)
    # Assert paths are distinct.
    assert path_a != path_b
    assert str(path_a.parent) == str(path_b.parent)

# Sessions for different methods on the same website must be isolated.
def test_session_method_isolation(tmp_path: Path):
    # Compute path for playwright_mcp.
    path_mcp = session_path("https://example.com", "playwright_mcp", root=tmp_path)
    # Compute path for browser_use.
    path_bu = session_path("https://example.com", "browser_use", root=tmp_path)
    # Assert methods use separate subdirectories.
    assert path_mcp != path_bu
    assert "playwright_mcp" in str(path_mcp)
    assert "browser_use" in str(path_bu)

# has_session correctly reports presence of session files.
def test_has_and_clear_session(tmp_path: Path):
    site = "https://test.example"
    method = "browser_use"
    # Empty before creation.
    assert has_session(site, method, root=tmp_path) is False
    # Ensure directory created.
    sdir = ensure_session_dir(site, method, root=tmp_path)
    assert sdir.is_dir()
    # Still empty because no files.
    assert has_session(site, method, root=tmp_path) is False
    # Create cookie file.
    (sdir / "cookies.json").write_text("{}")
    assert has_session(site, method, root=tmp_path) is True
    # Clear session.
    deleted = clear_session(site, method, root=tmp_path)
    assert deleted is True
    assert has_session(site, method, root=tmp_path) is False

# clear_all_sessions removes all stored sessions across methods.
def test_clear_all_sessions(tmp_path: Path):
    # Create sessions across two methods.
    dir1 = ensure_session_dir("https://one.example", "browser_use", root=tmp_path)
    (dir1 / "data.txt").write_text("data")
    dir2 = ensure_session_dir("https://two.example", "playwright_cli", root=tmp_path)
    (dir2 / "data.txt").write_text("data")
    # Clear all sessions.
    count = clear_all_sessions(root=tmp_path)
    assert count == 2
    assert not dir1.exists()
    assert not dir2.exists()
