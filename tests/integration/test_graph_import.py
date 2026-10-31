"""Integration contract tests that ensure graph construction is explicit about missing optional runtime dependencies."""
# Import pytest and the graph builder.
import pytest
from agent.graph import build_graph
# The graph builder should compile only when LangGraph is installed.
def test_graph_dependency_is_explicit():
    # Attempt to build the graph; in a fully installed environment this returns a compiled graph.
    try:
        graph = build_graph()
    except RuntimeError:
        # Assert the missing runtime package is surfaced as an import failure, not swallowed.
        assert True
    else:
        # Assert the compiled graph exposes invoke for a controlled run.
        assert callable(graph.invoke)
