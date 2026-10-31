"""Compile bounded LangGraph cycles with ephemeral runtime dependencies.

The controller repeats checkpointed cycles until a concrete end or assistance state.
There is no arbitrary global 50-transition limit and no persisted provider credential.
"""
# Explicit channels preserve actual failures and outcomes.
from agent.state import AgentState
# Share one workflow implementation across providers and browser methods.
from agent.nodes import plan_node, observe_node, decide_node, act_node, verify_node, progress_node, recover_node


# Construct the actual LangGraph cycle.
def build_graph():
    """Compile one observe/decide/act/verify or recovery cycle with runtime injection."""
    # Load orchestration only when a run actually requires it.
    try:
        # Keep browser-specific transports out of graph construction.
        from langgraph.graph import StateGraph, END
        # Runtime context carries SDK clients without checkpoint serialization.
        from langgraph.runtime import Runtime
    # Missing orchestration is a setup failure, not an invitation to substitute a loop library.
    except ImportError as exc:
        # Preserve actionable dependency guidance.
        raise RuntimeError("LangGraph is missing. Install project dependencies.") from exc

    # Adapt pure node functions to the current ephemeral runtime context.
    def wrapped(function):
        """Inject selected adapter/provider/store only for the duration of a node call."""
        # The annotated runtime parameter is injected by LangGraph.
        def invoke(state, runtime: Runtime):
            """Combine serializable state and runtime services without persisting handles."""
            # Nodes return data updates only, never the combined runtime mapping.
            return function({**state, **(runtime.context or {})})
        # Expose the adapted node.
        return invoke
    # Define data state and independent run context.
    graph = StateGraph(AgentState, context_schema=dict)
    # Register explicit stages for actionable diagnostics and tests.
    for name, function in (("plan", plan_node), ("observe", observe_node), ("decide", decide_node), ("act", act_node), ("verify", verify_node), ("progress", progress_node), ("recover", recover_node)):
        # All combinations receive exactly the same dependency injection.
        graph.add_node(name, wrapped(function))
    # Each bounded cycle starts with a fresh or reusable observation.
    graph.set_entry_point("plan")
    # Every cycle retains the compiled plan before observing the current UI.
    graph.add_edge("plan", "observe")
    # Stop/assistance/failure routing occurs before another model request.
    graph.add_conditional_edges("observe", _route_failure_or("decide"), {"decide": "decide", "recover": "recover", "end": END})
    # Valid decisions pass through explicit action handling, including terminal proposals.
    graph.add_conditional_edges("decide", _route_failure_or("act"), {"act": "act", "recover": "recover", "end": END})
    # Successful input must be verified against actual browser state.
    graph.add_conditional_edges("act", _route_failure_or("verify"), {"verify": "verify", "recover": "recover", "end": END})
    # A verified cycle returns state to the controller checkpoint loop.
    graph.add_conditional_edges("verify", _route_failure_or("progress"), {"recover": "recover", "progress": "progress", "end": END})
    # Progress measurement closes this bounded cycle before another model request.
    graph.add_edge("progress", END)
    # Recovery retains its concrete diagnostic before the next fresh cycle.
    graph.add_edge("recover", END)
    # Return the compiled LangGraph implementation.
    return graph.compile()


# Share terminal, assistance, and failure routing.
def _route_failure_or(next_node):
    """Build a router that never continues automatic input through a waiting state."""
    # Bind the normal destination without repeating policy.
    def route(state):
        """Choose a concrete next stage from actual execution state."""
        # Freeze automatic execution while awaiting a user decision.
        if state.get("finished") or state.get("stopped") or state.get("waiting"):
            # The controller owns finalization or resumption.
            return "end"
        # Preserve specific failed-operation state for bounded recovery.
        if state.get("last_error"):
            # Count real failures before another attempt.
            return "recover"
        # Continue the normal cycle.
        return next_node
    # Return the graph-compatible callback.
    return route


# Preserve explicit decision routing for isolated contract checks.
def _route_decision(state):
    """Route valid proposals through act_node rather than accepting nonempty output."""
    # Apply the same terminal and failure policy.
    return _route_failure_or("act")(state)


# Describe recovery continuation for callers inspecting the graph contract.
def _route_recovery(state):
    """End terminal recovery or begin a fresh observation cycle."""
    # The controller never restarts an exhausted or stopped run automatically.
    return "end" if state.get("finished") or state.get("stopped") else "observe"
