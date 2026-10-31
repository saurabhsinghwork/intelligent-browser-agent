"""Streamlit website-first experience, exclusive configuration, and live run controls.

The UI never runs browser/model loops directly. One process supervisor owns the
selected run; fragments poll safe events and render source artifacts without
rewriting them or claiming success from nonempty output.
"""
# Read complete current-run exports only when the user views/downloads them.
from pathlib import Path
# Render local application controls and periodic progress refresh.
import streamlit as st
# Serialize diagnostic data and constraint representations safely.
import json
# Validate the sole selected provider, executor, visibility, and runtime key.
from config.settings import RunConfiguration
# Use real keyless website discovery.
from services.website_discovery import search_websites
# Own actual worker lifecycle across Streamlit reruns.
from services.worker import RunSupervisor
# Keep session clearing explicit and scoped to application-managed profiles.
from browser.session_manager import clear_all_sessions


# Update one exclusive choice before Streamlit redraws checkbox widgets.
def _choose(group, selected, choices):
    """Select exactly one checkbox in a group without permitting an empty active choice."""
    # Persist the logical selection for configuration validation.
    st.session_state[group] = selected
    # Synchronize all sibling checkbox values before their next render.
    for choice in choices:
        # Clicking an alternative selects it; clicking the current choice keeps one active.
        st.session_state[group + "_" + choice] = choice == selected


# Build the complete local application without embedding implementation controls in task flow.
def render_app():
    """Render discovery, explicit website selection, task entry, and one active run."""
    # Initialize session state once without overwriting current-run ownership on reruns.
    defaults = {"provider": "gemini", "method": "playwright_mcp", "candidates": [], "selected_url": None, "search_attempted": False, "supervisor": None, "gemini_key": "", "groq_key": "", "show_browser_window": True}
    # Keep user inputs and active worker handles through ordinary UI reruns.
    for key, value in defaults.items():
        # Existing values belong to the user/current run.
        if key not in st.session_state:
            # Populate only missing defaults.
            st.session_state[key] = value
    # Synchronize real process state before enabling Start or session clearing.
    supervisor = st.session_state.supervisor
    # A task remains active while its owned process is actually alive.
    active = bool(supervisor and supervisor.poll().active)
    # Apply visual fading, hide Ctrl+Enter instructions everywhere, and support Enter-to-submit.
    st.markdown(
        """<style>
        div[data-testid='stCheckbox']:has(input:not(:checked)){opacity:.55}
        div[data-testid='stTextInput']:has(input:disabled){opacity:.4}
        div[data-testid='InputInstructions'], .stTextArea [data-testid='InputInstructions'], .stTextInput [data-testid='InputInstructions'] {
            display: none !important;
        }
        iframe[height="0"] { display: none !important; }
        </style>""",
        unsafe_allow_html=True,
    )
    # Import Streamlit components to inject client-side keyboard listener.
    import streamlit.components.v1 as components
    # Inject client-side JavaScript to allow Enter key to submit inputs without Ctrl+Enter.
    components.html(
        """<script>
        (function() {
            const parentDoc = window.parent.document;
            function attachEnterHandler() {
                const textareas = parentDoc.querySelectorAll('textarea');
                textareas.forEach(function(ta) {
                    if (ta.dataset.enterBound === 'true') return;
                    ta.dataset.enterBound = 'true';
                    ta.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
                            e.preventDefault();
                            const event = new KeyboardEvent('keydown', {
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                ctrlKey: true,
                                bubbles: true,
                                cancelable: true
                            });
                            ta.dispatchEvent(event);
                            ta.blur();
                        }
                    });
                });
                const instructions = parentDoc.querySelectorAll('[data-testid="InputInstructions"]');
                instructions.forEach(function(el) {
                    el.style.display = 'none';
                });
            }
            attachEnterHandler();
            const observer = new MutationObserver(attachEnterHandler);
            observer.observe(parentDoc.body, { childList: true, subtree: true });
        })();
        </script>""",
        height=0,
        width=0,
    )
    # Make the application purpose clear without exposing internal implementation jargon.
    st.title("Intelligent Browser Agent")
    # Describe the agreed initial release.
    st.caption("Search, navigate, filter, and collect complete source information without summarization.")
    # Keep provider, executor, and visibility choices in the left sidebar.
    with st.sidebar:
        # Present the two correctly named providers.
        st.subheader("Model provider")
        # Initialize exclusive provider checkbox values.
        for provider, label in (("gemini", "Gemini API"), ("groq", "Groq API")):
            # Keep widget state consistent with the single logical selection.
            st.session_state.setdefault("provider_" + provider, st.session_state.provider == provider)
            # Alternatives remain switchable while an active run locks configuration.
            st.checkbox(label, key="provider_" + provider, disabled=active, on_change=_choose, args=("provider", provider, ("gemini", "groq")))
        # Show the fixed model without adding a model-selection UI.
        st.caption("Gemini: 3.5 Flash-Lite · Groq: Qwen 3.8 27B")
        # Keep credentials masked and activate only the selected provider field.
        st.text_input("Gemini API key", type="password", key="gemini_key", disabled=active or st.session_state.provider != "gemini")
        # Do not label Groq as xAI Grok.
        st.text_input("Groq API key", type="password", key="groq_key", disabled=active or st.session_state.provider != "groq")
        # Expose exactly the three agreed executor choices.
        st.subheader("Browser method")
        # Synchronize an exclusive group while retaining the checkbox appearance.
        for method, label in (("playwright_mcp", "Agent + Playwright MCP"), ("playwright_cli", "Agent + Playwright CLI"), ("browser_use", "Browser Use")):
            # Initialize widgets only once.
            st.session_state.setdefault("method_" + method, st.session_state.method == method)
            # One method owns each run; no silent substitutes exist.
            st.checkbox(label, key="method_" + method, disabled=active, on_change=_choose, args=("method", method, ("playwright_mcp", "playwright_cli", "browser_use")))
        # Use one visibility toggle as specified rather than two independent flags.
        headful = st.toggle("Show browser window", key="show_browser_window", disabled=active)
        # Explain the actual effect of the selected mode.
        st.caption("Visible interactions" if headful else "Background execution; visible assistance is available when required.")
        # Keep profile management explicit and unavailable while a run owns a profile.
        with st.expander("Saved sessions"):
            # Never clear profiles concurrently with an active browser.
            if st.button("Clear saved sessions", disabled=active):
                # The session service validates every recursive removal boundary.
                count = clear_all_sessions()
                # Report only profiles actually removed.
                st.info(f"Cleared {count} saved sessions.")
    # Website discovery comes before any task execution.
    st.subheader("1. Choose a website")
    # Keep search independent of model-key availability.
    query = st.text_input("Website name or domain", placeholder="For example: flikart", disabled=active)
    # Search happens only after an explicit user action.
    if st.button("Search", disabled=active or not query.strip()):
        # Clear old selection so new search results cannot silently choose a website.
        st.session_state.selected_url = None
        # Distinguish no-results feedback from an untouched initial page.
        st.session_state.search_attempted = True
        # Show bounded real search work without fabricating filler domains.
        try:
            # Display activity while the actual search service responds.
            with st.spinner("Searching for relevant websites…"):
                # No provider key is required by discovery.
                st.session_state.candidates = search_websites(query)
        # Keep a failed search distinct from a guessed website suggestion.
        except Exception as exc:
            # Do not retain misleading results from an earlier query.
            st.session_state.candidates = []
            # Discovery exceptions contain safe actionable guidance.
            st.error(str(exc))
    # Offer explicit selection with no automatic first result.
    if st.session_state.candidates:
        # Preserve actual candidate URLs as radio values.
        urls = [candidate.url for candidate in st.session_state.candidates]
        # Keep names and exact destinations visible.
        labels = {candidate.url: candidate.name + " — " + candidate.url for candidate in st.session_state.candidates}
        # index=None requires the user's intended destination choice.
        st.radio("Select the intended website", urls, index=None, format_func=lambda url: labels[url], key="selected_url", disabled=active)
        # Fewer real results are more honest than invented domains.
        if len(urls) < 3:
            # Explain search availability without presenting fabricated matches.
            st.caption("The search returned fewer than three distinct websites.")
    # Show no-results guidance only after the user actually searched.
    elif st.session_state.search_attempted:
        # Preserve the website-first workflow.
        st.info("No verified search suggestions were returned. Try a more specific name or a full URL.")
    # Task input is available only after explicit website selection.
    st.subheader("2. Describe your task")
    # Preserve the user's original instruction across configuration changes.
    task = st.text_area("What should the agent retrieve?", key="task_input", disabled=active or not st.session_state.selected_url, height=110)
    # Display intelligent query refinement and execution contract when task is entered.
    if task.strip():
        # Import intelligent task refiner.
        from agent.refiner import refine_task
        # Parse and disambiguate user query.
        refinement = refine_task(task, st.session_state.selected_url)
        # Display understood task contract in a clean container.
        with st.expander("🧠 Intelligent Task Refinement & Execution Contract", expanded=True):
            # Display clarified objective.
            st.markdown(f"**Understood Goal:** {refinement['clarified_objective']}")
            # Display metrics columns.
            cols = st.columns(4)
            # Show entity metric.
            cols[0].metric("Entity", refinement["entity"].title())
            # Show count metric.
            cols[1].metric("Target Count", refinement["required_count"] or "All")
            # Show detail level.
            cols[2].metric("Detail Level", refinement["detail_level"].title())
            # Show selected strategy.
            cols[3].metric("Strategy", refinement["strategy"].title())
            # Show constraints if present.
            if refinement["constraints"]:
                # Render constraints json.
                st.caption(f"Constraints: {json.dumps(refinement['constraints'])}")
            # Show deterministic execution steps.
            if refinement["execution_steps"]:
                # Section heading.
                st.markdown("**Deterministic Execution Plan (Zero Hallucination):**")
                # Iterate each step.
                for idx, step in enumerate(refinement["execution_steps"], 1):
                    # Render numbered step.
                    st.markdown(f"{idx}. {step}")
    # Use only the selected provider's runtime credential.
    key = st.session_state.gemini_key if st.session_state.provider == "gemini" else st.session_state.groq_key
    # Disable Start until the agreed website-first configuration is complete.
    ready = bool(st.session_state.selected_url and task.strip() and key.strip())
    # One supervisor owns a run until actual process exit.
    if st.button("Start task", type="primary", disabled=active or not ready):
        # Keep runtime-only credentials out of persisted configuration representations.
        configuration = RunConfiguration(st.session_state.provider, st.session_state.method, headful, key)
        # Start the worker without blocking monitoring or Stop behind browser/model calls.
        st.session_state.supervisor = RunSupervisor(task, st.session_state.selected_url, configuration)
        # Redraw configuration immediately as locked while the worker is active.
        st.rerun()
    # Live monitoring remains independent of slow browser/provider operations.
    _render_monitoring()


# Refresh progress and controls while the worker continues independently.
@st.fragment(run_every="1s")
def _render_monitoring():
    """Poll safe events, expose explicit assistance controls, and render faithful artifacts."""
    # There is no current run before the first explicit Start.
    supervisor = st.session_state.get("supervisor")
    # Keep the initial application simple.
    if supervisor is None:
        # Avoid empty monitoring controls.
        return
    # Drain events without blocking on the worker.
    monitor = supervisor.poll()
    # A fragment-only completion must re-enable configuration in the full application.
    was_active = st.session_state.get("last_run_active", False)
    # Remember actual process ownership for the next periodic refresh.
    st.session_state.last_run_active = monitor.active
    # Refresh disabled sidebar/Start controls only after real worker exit.
    if was_active and not monitor.active:
        # Preserve the completed result while redrawing the full application.
        st.rerun(scope="app")
    # Read a consistent detached snapshot.
    snapshot = monitor.snapshot()
    # Display actual lifecycle status.
    st.subheader("Current run")
    # Never claim completion from an available text result alone.
    st.write(snapshot["status"])
    # Keep pause and cancellation distinct.
    columns = st.columns(3)
    # Pause freezes work without releasing worker ownership.
    if columns[0].button("Pause", disabled=not monitor.active or bool(snapshot["waiting"])):
        # The worker checks this inside local traversal and before nodes.
        supervisor.pause()
    # Stop starts bounded owned-resource cleanup.
    if columns[1].button("Stop", disabled=not monitor.active):
        # Do not re-enable configuration until the actual process has exited.
        supervisor.stop()
    # Reset affects only displayed current-run state after resources are released.
    if columns[2].button("Reset", disabled=monitor.active):
        # Starting over never kills an unrelated browser session.
        st.session_state.supervisor = None
        # Refresh the whole application to restore the initial controls.
        st.rerun(scope="app")
    # Display concrete waiting requests without auto-approving preselected choices.
    request = snapshot["waiting"]
    # Human-only steps remain part of the same active run.
    if request:
        # Explain exactly why execution is paused.
        st.info(request.get("message") or "Waiting for " + request["kind"])
        # New hostnames require an explicit run-scoped authorization.
        if request["kind"] == "hostname":
            # Show the actual proposed destination before accepting navigation.
            st.write(request["url"])
            # Grant only this concrete requested hostname.
            if st.button("Authorize this hostname"):
                # The worker reapplies policy and re-observes after the response.
                supervisor.respond({"action": "authorize"})
            # Refusal retains any already collected partial content.
            if st.button("Decline"):
                # Never silently expand the website boundary.
                supervisor.respond({"action": "deny"})
        # Potentially non-finite content needs an explicit collection criterion.
        elif request["kind"] == "scope_limit":
            # Explain that this is a user-selected bound rather than exhaustive completion.
            limit = st.number_input("Maximum total traversal actions for this page", min_value=1, value=100, step=10)
            # Only submission supplies a criterion.
            if st.button("Continue with this limit"):
                # Preserve the chosen limit in checkpoint state.
                supervisor.respond({"action": "resume", "limit": int(limit)})
        # Login/CAPTCHA and ordinary Pause resume only after the user is ready.
        elif st.button("Resume"):
            # The selected worker re-observes the actual browser before acting.
            supervisor.respond({"action": "resume"})
    # Render safe events using explicit dictionaries rather than indexing RunEvent objects.
    with st.expander("Logs", expanded=False):
        # Keep rendering bounded while the full JSONL log stays on disk.
        st.code("\n".join(event["timestamp"] + " [" + event["level"] + "] " + event["message"] for event in snapshot["events"][-200:]), language=None)
    # Preserve the current run's full screenshot inventory without loading every image every second.
    with st.expander("Screenshots", expanded=False):
        # Display captured observations progressively.
        if snapshot["screenshots"]:
            # Let the user inspect any immutable image from this run.
            index = st.slider("Captured view", 1, len(snapshot["screenshots"]), len(snapshot["screenshots"])) if len(snapshot["screenshots"]) > 1 else 1
            # Load only the chosen actual viewport image.
            st.image(snapshot["screenshots"][index - 1])
    # Terminal results reference complete exports instead of model-generated summaries.
    result = monitor.result
    # Keep configuration locked until actual worker cleanup finishes.
    if result and not monitor.active:
        # Show verified completion separately from partial evidence.
        st.subheader("Result")
        # A blocker cannot erase already captured source data.
        if result.get("blocker"):
            # Explain limitations outside the verbatim source body.
            st.warning(result["blocker"])
        # Only independently checked coverage/fidelity can receive a complete label.
        elif result.get("verified"):
            # Keep the completion claim precise.
            st.success("Completed with source and traversal evidence.")
        # Preserve the distinction between stopped and verified tasks.
        else:
            # Available artifacts may still contain useful partial information.
            st.info("Partial or unverified source information.")
        # Read complete local artifacts without applying model token limits.
        artifacts = result.get("artifacts") or {}
        # TXT is the authoritative exact captured-text view.
        text_path = Path(artifacts["text"]) if artifacts.get("text") else None
        # A forced stop may occur before a text export was available.
        if text_path and text_path.is_file():
            # Preserve source whitespace and literal JSON in the main view.
            content = text_path.read_text(encoding="utf-8")
            # Never reinterpret source content as executable HTML.
            st.code(content, language=None, wrap_lines=True)
            # Offer a complete export rather than truncating large results.
            st.download_button("Download exact text", content.encode("utf-8"), file_name="result.txt", mime="text/plain")
        # Markdown is a separate structural companion, not a replacement for exact text.
        if artifacts.get("markdown") and Path(artifacts["markdown"]).is_file():
            # Preserve the worker's deterministic structural export.
            data = Path(artifacts["markdown"]).read_bytes()
            # Do not generate a new summary during download.
            st.download_button("Download Markdown", data, file_name="result.md", mime="text/markdown")
        # Coverage and exact cell relationships remain independently inspectable.
        if artifacts.get("manifest") and Path(artifacts["manifest"]).is_file():
            # Preserve machine-readable provenance for debugging and acceptance.
            st.download_button("Download source manifest", Path(artifacts["manifest"]).read_bytes(), file_name="manifest.json", mime="application/json")
