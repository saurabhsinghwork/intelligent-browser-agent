"""Evidence-backed nodes shared by both providers and all browser methods.

Runtime dependencies are injected outside persisted graph state. Final output is
assembled from captured source; model text and tool success alone prove nothing.
"""
# Normalize data-only records for checkpointing.
from dataclasses import asdict, replace
# Avoid fragment-only crawl loops while preserving meaningful query parameters.
from urllib.parse import urldefrag
# Supply compact collection progress without retransmitting complete source transcripts.
import json
# Respect an explicit single-page boundary when deciding whether traversal is finished.
import re
# Sanitize useful error details instead of losing the cause.
from domain.events import redact_secrets
# Share typed observations and constrained actions.
from domain.models import AgentDecision, BrowserObservation
# Route human-only conditions separately from ordinary retries.
from domain.errors import AssistanceRequired, AuthorizationRequired, ProviderConfigurationError
# Validate even decisions produced by injected custom providers.
from agent.validation import validate_decision
# Count no more than five total failures for the same unresolved problem.
from config.constants import MAX_ATTEMPTS_PER_DECISION
# Compile and enforce the generalized task plan inside LangGraph state.
from agent.goals import action_policy, build_plan, compile_goal, measure_progress
# Compare pages independently from fragments, tracking fields, and sibling subdomains.
from services.identity import canonical_url
# Dismiss optional rendered overlays through the same grounded native input path.
from services.interruptions import dismiss_observed_interruption


# Compile one stable goal and plan before the first observation cycle.
def plan_node(state):
    """Create the generalized completion contract once and retain it across cycles."""
    # Existing checkpointed plans must remain stable during retries and page changes.
    if state.get("goal") and state.get("plan"):
        # No update is needed after the initial compilation.
        return {}
    # Compile explicit count, entity, constraints, fields, and action boundaries.
    goal = compile_goal(state.get("task", ""))
    # Build measurable ordered phases without tying them to one website.
    plan = build_plan(goal)
    # Start with an empty evidence-backed progress ledger.
    progress = measure_progress(goal, [], {})
    # Publish JSON-safe state for every later LangGraph node.
    return {"goal": goal, "plan": plan, "progress": progress, "action_memory": [], "status": "Task plan prepared"}


# Measure task advancement after independent browser-effect verification.
def progress_node(state):
    """Update record counts and remember whether the last action advanced the objective."""
    # Read durable source evidence when the current run owns a store.
    blocks = state["store"].blocks() if state.get("store") is not None else []
    # Compare qualifying unique records against the previous compact ledger.
    progress = measure_progress(state.get("goal", {}), blocks, state.get("progress", {}))
    # Retain a bounded action memory for repeated no-progress rejection.
    memory = list(state.get("action_memory", []))
    # Read the attempted action and current canonical page state.
    decision = state.get("decision", {})
    # Record only concrete browser or collection operations.
    if decision.get("kind"):
        # Bind repetition to the exact action, target/value, canonical page, and observed fingerprint.
        memory.append({"kind": decision.get("kind"), "target": decision.get("target", ""), "value": decision.get("value", ""), "page": canonical_url(state.get("observation", {}).get("url", "")), "fingerprint": state.get("observation", {}).get("fingerprint", ""), "advanced": bool(progress.get("advanced"))})
        # Keep sufficient recent strategy evidence without growing checkpoints indefinitely.
        memory = memory[-40:]
    # A finite completed goal no longer needs queued exploratory destinations.
    updates = {"progress": progress, "action_memory": memory}
    # Remove irrelevant remaining frontier work once the measured predicate is met.
    if progress.get("complete"):
        # Let the next cycle enter deterministic finish verification.
        updates.update({"frontier": [], "status": "Requested records collected; verifying completion"})
    # Return only compact task-progress updates.
    return updates


# Read Stop without depending on presentation internals.
def _stopped(state):
    """Return whether the injected cancellation event is set."""
    # Pause before another node can invoke a model or dispatch browser input.
    monitor = state.get("monitor")
    # Direct node tests may omit the worker control channel.
    if monitor is not None and hasattr(monitor, "gate"):
        # The monitor waits only while Pause is active and still observes Stop.
        monitor.gate()
    # Optional runtime dependencies keep isolated node tests lightweight.
    event = state.get("stop_event")
    # A missing event is not cancellation.
    return bool(event and event.is_set())


# Publish concise live progress through the current run's monitor.
def _publish(state, message, level="INFO"):
    """Update status and record a distinct warning/error when monitoring exists."""
    # Keep monitoring outside the serializable graph contract.
    monitor = state.get("monitor")
    # Direct node tests may omit presentation collaborators.
    if monitor is not None:
        # Event creation performs secret redaction.
        monitor.update_status(message)
        # Preserve meaningful warning/error severity.
        if level != "INFO":
            # Do not expose private chain-of-thought or SDK request bodies.
            monitor.log(level, message)


# Normalize observations without modifying source whitespace.
def _observation_dict(observation):
    """Copy a shared record or compatible mapping into serializable state."""
    # Dataclasses contain only observation data.
    if isinstance(observation, BrowserObservation):
        # Preserve geometry, source text, and screenshot identity.
        return asdict(observation)
    # Keep controller-injected mappings compatible.
    return dict(observation)


# Preserve concrete errors in declared graph channels.
def _failure(prefix, exc):
    """Return bounded sanitized diagnostics and require a fresh recovery observation."""
    # Retain actionable context without dumping private response payloads.
    detail = redact_secrets(str(exc))[:350]
    # Honor quota/server backoff rather than sending five immediate identical requests.
    status = getattr(exc, "status_code", getattr(exc, "code", None))
    # Default to a short exponential cooldown only for transient provider HTTP failures.
    retry_delay = 2.0 if status == 429 or isinstance(status, int) and status >= 500 else 0.0
    # A provider's explicit Retry-After overrides the default when numeric.
    if retry_delay:
        # The response object is inspected only for its public timing header.
        headers = getattr(getattr(exc, "response", None), "headers", {})
        # Invalid timing metadata must not hide the original provider failure.
        try:
            # Bound one delay while allowing the user to cancel it promptly.
            retry_delay = min(300.0, max(retry_delay, float(headers.get("retry-after", 0))))
        # An HTTP-date or malformed header falls back to the short bounded cooldown.
        except (TypeError, ValueError):
            # Preserve the safe default rather than repeating a request immediately.
            pass
    # Keep error state distinct from successful output.
    return {"last_error": f"{prefix}: {type(exc).__name__}: {detail}", "retry_delay": retry_delay, "status": prefix, "observation_ready": False}


# Distinguish explicit page requests from broader website/tutorial exploration.
def _page_only_task(task):
    """Honor phrases such as 'from that page' without changing broader website tasks."""
    # Only explicit page-scoped wording overrides automatic relevant-link exploration.
    return bool(re.search(r"\b(?:from|on|in)\s+(?:(?:the\s+)?(?:this|that|current|selected)|the)?\s*page\b|\b(?:this|that|current|selected)\s+page\s+only\b", task, re.I))


# Collect exact source through the selected executor.
def _collect(state, scope):
    """Return coverage/frontier/artifact updates after measured local traversal."""
    # Import lazily to avoid adapter/service cycles.
    from services.extraction import collect_page
    # The durable store exists outside compact model observations.
    store = state.get("store")
    # Normalize only fragments for page identity.
    url = canonical_url(state["observation"]["url"])
    # Preserve actual traversal order.
    visited = list(state.get("visited", []))
    # Record each source page once.
    if url not in visited:
        # Retain stable page ordering across retries.
        visited.append(url)
    # A page-specific task must not traverse a site's unrelated navigation sidebar.
    page_only = _page_only_task(state.get("task", ""))
    # Remember whether the model explicitly selected one semantic detail-page region.
    detail_region = state.get("goal", {}).get("detail_level") == "full" and scope in {"main", "article", "[role=main]", "__iba_page_content__"}
    # Full-detail goals should collect the richest visible nested detail interface, not listing cards.
    if state.get("goal", {}).get("detail_level") == "full" and scope in {"", "body", "window", "main", "article", "[role=main]", "__iba_page_content__"}:
        # Read real observed nested scroll regions from the current browser geometry.
        containers = [item for item in [*state.get("observation", {}).get("geometry", {}).get("containers", []), *state.get("observation", {}).get("geometry", {}).get("regions", [])] if item.get("id") != "window" and str(item.get("text", "")).strip()]
        # Rank one observed scroll region by rendered detail richness.
        def detail_score(item):
            """Prefer description/requirements regions over repeated result-card lists."""
            # Normalize only for matching while preserving exact source separately.
            text = str(item.get("text", "")).lower()
            # Common information-detail markers work across products, jobs, articles, and similar records.
            markers = sum(1 for phrase in ("description", "responsibilities", "qualifications", "requirements", "about", "skills", "employment type", "seniority", "show more", "details") if phrase in text)
            # Favor semantic richness first and bounded rendered length second.
            return markers * 10000 + min(len(text), 5000)
        # Bind collection to the richest actual current nested region when available.
        if containers:
            # Use its stable observed DOM identity rather than a website selector.
            scope = max(containers, key=detail_score)["id"]
            # The selected observed panel is one explicitly bounded detail interface.
            detail_region = True
    # Resolve semantic main/article requests to real landmarks and common main-content IDs.
    if scope in {"main", "article", "[role=main]"} or page_only and (not scope or scope == "body"):
        # This application-owned scope resolves a unique main/article region, with body fallback.
        scope = "__iba_page_content__"
    # Check if specialized LinkedIn strategy matches the current task or page.
    from agent.strategies.linkedin import LinkedInStrategy
    # Use specialized master-detail traversal for LinkedIn tasks.
    if LinkedInStrategy.matches(state.get("goal"), url):
        # Execute generalized LinkedIn master-detail extraction.
        report = LinkedInStrategy.collect_jobs(state["adapter"], state.get("goal"), store, state.get("monitor"))
    # Otherwise use standard measured page traversal.
    else:
        # Scroll and collect locally, without model calls per mechanical step.
        report = collect_page(state["adapter"], scope or "body", store, visited.index(url), state.get("scroll_limit"), state.get("goal"), detail_region)
    # Preserve compact coverage independently of source blocks.
    pages = dict(state.get("collected_pages", {}))
    # Keep evidence manifests small enough for checkpointed orchestration.
    pages[url] = {key: value for key, value in report.items() if key not in {"blocks", "links", "screenshots"}}
    # Retain every real candidate before bounded relevance review.
    discovered = {item["url"]: item for item in state.get("discovered_links", [])}
    # Include links discovered after lazy loading and scrolling.
    for link in ([] if page_only or state.get("goal", {}).get("detail_level") == "full" else report["links"]):
        # Preserve query parameters and exact hostnames.
        destination = canonical_url(link["url"])
        # Keep first source ordering rather than sorting URLs alphabetically.
        discovered.setdefault(destination, {**link, "url": destination, "source": url})
    # Export complete artifacts incrementally when a durable store exists.
    artifacts = store.export(state.get("goal")) if store is not None else {}
    # Isolated collectors may return exact block text without SQLite.
    output = store.text(state.get("goal")) if store is not None else "\n\n".join(block["text"] for block in report["blocks"])
    # Reuse the collector's final matching source/screenshot state instead of rereading the same page.
    final_observation = getattr(state["adapter"], "_collection_observation", None)
    # Preserve the prior state only if an injected adapter did not publish a final capture.
    observation = asdict(final_observation) if final_observation is not None else state.get("observation", {})
    # If final observation has a distinct URL, record it in collected_pages too.
    if final_observation is not None:
        # Canonicalize the observed final URL.
        obs_url = canonical_url(final_observation.url)
        # Add new page entry if not already present.
        if obs_url and obs_url not in pages:
            # Copy existing page attributes.
            pages[obs_url] = dict(pages.get(url, {}))
    # Traversal publishes a fresh reusable observation alongside exact source evidence.
    # Count qualifying records immediately so finite tasks can stop before link review.
    progress = measure_progress(state.get("goal", {}), store.blocks() if store is not None else report["blocks"], state.get("progress", {}))
    # If the finite goal is complete, synchronize all recorded pages as complete.
    if progress.get("complete") or bool(report.get("complete") or report.get("task_complete")):
        # Mark all visited pages as complete.
        for page_data in pages.values():
            # Set page complete flag.
            page_data["complete"] = True
            # Set task complete flag.
            page_data["task_complete"] = True
    # A page boundary or satisfied finite goal exhausts unnecessary exploration.
    stop_frontier = page_only or progress.get("complete") or bool(report.get("complete") or report.get("task_complete"))
    # Return coverage, output, and compact measurable progress together.
    return {"collected_pages": pages, "visited": visited, "discovered_links": [] if stop_frontier else list(discovered.values()), **({"frontier": []} if stop_frontier else {}), "screenshots": [*state.get("screenshots", []), *report["screenshots"]], "output": output, "artifacts": artifacts, "observation": observation, "observation_ready": final_observation is not None, "progress": progress}


# Observe once, reusing fresh post-action observations when possible.
def observe_node(state):
    """Capture the actual browser or retain a current verification observation."""
    # Stop before any new browser/model call.
    if _stopped(state):
        # Preserve honest terminal cancellation.
        return {"stopped": True, "finished": True, "verified": False, "status": "Stopped by user"}
    # Avoid duplicate screenshot/DOM work between graph cycles.
    if state.get("observation_ready") and state.get("observation"):
        # Consume this reusable observation for the next decision.
        return {"observation_ready": False}
    # Expose work before a potentially slower tool operation.
    _publish(state, "Observing current browser state")
    # Normalize concrete adapter failures.
    try:
        # Use exactly the selected method.
        data = _observation_dict(state["adapter"].observe())
        # Reject ordinary optional-cookie notices without spending a model decision.
        reject = next((item for item in data.get("elements", []) if not item.get("disabled") and item.get("text", "").strip().lower() in {"reject all", "reject optional cookies", "necessary only", "only necessary", "use necessary cookies only"}), None)
        # Use the actual current input target rather than a text-searching animation.
        if reject is not None:
            # Keep consent behavior within the explicitly approved rejection policy.
            state["adapter"].execute(AgentDecision(kind="click", target=reject["id_label"], observation_id=data.get("observation_id", "")))
            # Reason only after observing the real resulting interface.
            data = _observation_dict(state["adapter"].observe())
        # Bound automatic HTML-overlay handling so a defective page cannot create an input loop.
        for _ in range(3):
            # Dismiss only recognized nonessential sign-in/promotion interruptions.
            dismissed, refreshed = dismiss_observed_interruption(state["adapter"], data, state.get("task", ""))
            # Always retain the freshest action-bound observation returned by dismissal handling.
            data = _observation_dict(refreshed)
            # Stop when no supported topmost overlay was closed.
            if not dismissed:
                # Continue reasoning as soon as no supported overlay remains.
                break
    # Cross-host navigation pauses rather than continuing silently.
    except AuthorizationRequired as exc:
        # Preserve the actual requested destination.
        return {"waiting": {"kind": "hostname", "url": exc.url}, "status": "Waiting for hostname authorization"}
    # Other failures enter bounded recovery.
    except Exception as exc:
        # Preserve the specific cause across nodes.
        return _failure("Observation failed", exc)
    # Retain immutable paths from this run only.
    screenshots = list(dict.fromkeys([*state.get("screenshots", []), *data.get("all_screenshots", []), *([data["screenshot_path"]] if data.get("screenshot_path") else [])]))
    # Do not erase the previous error before strategy adaptation can read it.
    return {"observation": data, "screenshots": screenshots, "observation_ready": False, "last_error": "", "status": "Observed " + data["url"]}


# Select a grounded action or classify a bounded discovered-link batch.
def decide_node(state):
    """Use one selected model; preserve ordinary actions even when output is empty."""
    # Do not dispatch another API request after Stop.
    if _stopped(state):
        # Preserve cancellation as a separate terminal outcome.
        return {"stopped": True, "finished": True, "status": "Stopped by user"}
    # Rebuild the explicit provider-neutral observation.
    observation = BrowserObservation(**state["observation"])
    # Track all candidates already classified or collected.
    reviewed = set(state.get("reviewed_links", [])) | set(state.get("visited", []))
    # Prompt limits cannot discard the remaining complete link frontier.
    batch = []
    # Preserve full URL strings while keeping each relevance-review request small.
    batch_size = 0
    # Unselected candidates remain pending for subsequent exact batches.
    for item in state.get("discovered_links", []):
        # Already reviewed or collected URLs cannot create crawl cycles.
        if item["url"] in reviewed:
            # Preserve the next actual unreviewed candidate.
            continue
        # Count the actual compact context, not the number of unrelated DOM nodes.
        size = len(json.dumps({"url": item["url"], "text": item.get("text", "")[:180]}, ensure_ascii=False))
        # Bound requests without silently discarding remaining candidates.
        if batch and (len(batch) >= 30 or batch_size + size > 6000):
            # The next graph cycle handles the rest of the real frontier.
            break
        # Retain complete real destinations, never shortened or invented URLs.
        batch.append(item)
        # Track the encoded review payload size.
        batch_size += size
    # Start from the unchanged user objective.
    task = state["task"]
    # Tell the selected model which pages are actually captured and what work remains.
    current_url = canonical_url(observation.url)
    # Never drop a queued destination merely because its first navigation failed.
    frontier = [url for url in state.get("frontier", []) if url not in state.get("visited", [])]
    # Keep task-relevant coverage distinct from visible text on the current screen.
    task += "\nCompiled goal and plan: " + json.dumps({"goal": state.get("goal", {}), "plan": state.get("plan", []), "progress": state.get("progress", {})}, ensure_ascii=False)
    # Make the full-detail completion contract explicit when listing cards are insufficient.
    if state.get("goal", {}).get("detail_level") == "full":
        # Require a distinct expanded detail region/page for every requested entity.
        task += "\nFULL DETAIL MODE: Listing cards do not count. Open one not-yet-collected entity, expand safe Show more/Read more disclosures, then collect its specific detail panel or detail page. Repeat for distinct entities until measured progress reaches the requested count. Do not invent an unspecified search keyword."
    # Supply measured collection state separately from model-generated rationale.
    task += "\nMeasured collection state: " + json.dumps({"current_page_collected": current_url in state.get("collected_pages", {}) and not state.get("collected_pages", {}).get(current_url, {}).get("dirty"), "collected_pages": len(state.get("collected_pages", {})), "queued_pages": len(frontier), "instruction": "Choose the next plan step that measurably advances the goal. Use collect on a relevant region when records are visible. Use finish only after measured completion."})
    # A satisfied finite predicate needs no additional model navigation choice.
    if state.get("progress", {}).get("complete"):
        # Propose deterministic final verification against the evidence store.
        decision = AgentDecision(kind="finish", rationale="Measured completion predicate reached", expected="objective_met")
        # Skip another provider round trip after the requested count exists.
        return {"decision": asdict(decision), "frontier": [], "link_batch": [], "last_error": "", "status": "Verifying measured completion"}
    # Specialized strategy routing for LinkedIn master-detail tasks.
    from agent.strategies.linkedin import LinkedInStrategy
    # Check if LinkedIn strategy is active for this goal or page.
    if LinkedInStrategy.matches(state.get("goal"), current_url):
        # Read direct search URL if prepared by task refiner.
        direct_url = state.get("goal", {}).get("direct_url")
        # Direct navigation to pre-filtered search results if on landing page.
        if direct_url and ("jobs" not in current_url or ("keywords" not in current_url and "location" not in current_url)):
            # Navigate directly to pre-filtered results.
            decision = AgentDecision(kind="navigate", target=direct_url, rationale="Navigate to refined LinkedIn search URL")
            # Schedule direct navigation without extra reasoning latency.
            return {"decision": asdict(decision), "frontier": frontier, "link_batch": [], "last_error": "", "status": "Navigating to refined search URL"}
        # If already on LinkedIn search results page and not yet collected.
        if "jobs" in current_url and current_url not in state.get("collected_pages", {}):
            # Propose collect action to trigger LinkedIn master-detail strategy.
            decision = AgentDecision(kind="collect", target="master_detail", rationale="Collect full job records via LinkedIn Master-Detail strategy")
            # Trigger collection directly.
            return {"decision": asdict(decision), "frontier": frontier, "link_batch": [], "last_error": "", "status": "Executing LinkedIn master-detail extraction"}
    # Supply retained diagnostics for a revised strategy.
    if state.get("last_error"):
        # Make the concrete failed operation available without full SDK payloads.
        task += "\nPrevious failure: " + state["last_error"] + ". Revise your strategy."
    # Link classification happens on the same selected visual reasoning model.
    if batch:
        # Supply exactly the batch the model is permitted to select from.
        observation.links = batch
        # Keep exhaustive relevance accounting separate from final text generation.
        task += "\nLINK REVIEW ONLY: Return queue_links. Select every task-relevant URL from this exact batch, including relevant chapters/pagination. Exclude unrelated navigation and recommendation loops."
    # Advance a validated frontier mechanically without another decision request.
    elif frontier and current_url != frontier[0]:
        # Preserve source order for relevant pages.
        destination = frontier[0]
        # Use an ordinary action subject to the same hostname boundary.
        decision = AgentDecision(kind="navigate", target=destination, rationale="Visit queued relevant page")
        # Remove only the scheduled destination.
        return {"decision": asdict(decision), "frontier": frontier, "link_batch": [], "last_error": ""}
    # A queued destination can prove irrelevant after its actual page is observed.
    if not batch and frontier and current_url == frontier[0]:
        # Ask for an explicit scope revision instead of navigation back to a captured page.
        task += "\nThis is the currently queued page. If its actual content is irrelevant, return queue_links with target skip_current, links [], and a concrete rationale. Otherwise collect its relevant content. Do not navigate back to a previously collected page to dismiss this destination."
    # Publish one concise action-selection status.
    _publish(state, "Reviewing relevant links" if batch else "Choosing a grounded action")
    # Keep transport and malformed-response errors recoverable.
    try:
        # One provider handles both screenshots and reasoning.
        decision = state["provider"].decide(task, observation, state.get("history", []))
        # Custom/fake providers cannot bypass shared validation.
        validate_decision(decision)
        # Repair only a missing interactive ID when one quoted current label resolves uniquely.
        if decision.kind in {"click", "fill"} and decision.target not in {item.get("id_label") for item in observation.elements}:
            # Read explicit quoted control wording from the model's concise rationale.
            quoted = [value.strip() for value in re.findall(r"['\"]([^'\"]{1,80})['\"]", decision.rationale or "") if value.strip()]
            # Match exact visible labels on controls that currently receive pointer input.
            matches = [item for item in observation.elements if item.get("in_view") is not False and item.get("actionable") is not False and any(value.lower() in {str(item.get("text", "")).strip().lower(), str(item.get("aria_label", "")).strip().lower()} for value in quoted)]
            # A unique semantic match is safer than spending retries on a stale generated ID.
            if len(matches) == 1:
                # Preserve every decision field except the repaired current DOM identity.
                decision = replace(decision, target=matches[0]["id_label"], observation_id=observation.observation_id)
        # Apply deterministic information-only and constraint-preserving policy before execution.
        policy_error = action_policy(decision, observation, state.get("goal", {}))
        # A forbidden or conflicting control must be replanned rather than clicked.
        if policy_error:
            # Preserve a concrete strategy error for bounded recovery.
            raise ValueError(policy_error)
        # Build the action signature used for no-progress memory checks.
        signature = {"kind": decision.kind, "target": decision.target, "value": decision.value, "page": canonical_url(observation.url), "fingerprint": observation.fingerprint}
        # Reject an identical action that already failed to advance this same page state.
        if decision.kind in {"click", "fill", "navigate", "press", "switch_tab", "collect"} and any(all(item.get(key) == value for key, value in signature.items()) and not item.get("advanced") for item in state.get("action_memory", [])[-12:]):
            # Force a different grounded strategy instead of repeating clicks or fills.
            raise ValueError("This action already failed to advance the task in the same page state")
        # A relevance batch cannot be silently discarded by a finish reply.
        if batch and decision.kind != "queue_links":
            # Force explicit classification before scope completion.
            raise ValueError("Link review must return queue_links")
    # Model access/schema failures cannot be solved by repeated navigation attempts.
    except ProviderConfigurationError as exc:
        # Keep collected source available while clearly identifying the setup blocker.
        return {"finished": True, "verified": False, "blocker": str(exc), "status": "Provider setup required"}
    # Preserve actual error details instead of fabricating completion.
    except Exception as exc:
        # Re-observe and ask for a revised strategy within the failure budget.
        return _failure("Decision failed", exc)
    # Retain the exact supplied batch and normalized decision.
    return {"decision": asdict(decision), "frontier": frontier, "link_batch": batch, "last_error": "", "status": "Decided: " + decision.kind}


# Dispatch input, collection, relevance classification, and assistance explicitly.
def act_node(state):
    """Keep real blockers distinct from success and collect source before finalization."""
    # No further input may start after Stop.
    if _stopped(state):
        # Already committed evidence remains available.
        return {"stopped": True, "finished": True, "verified": False, "status": "Stopped by user"}
    # Rebuild the validated operation.
    decision = AgentDecision(**state["decision"])
    # Text length cannot transform a genuine blocker into success.
    if decision.kind == "blocked":
        # Preserve a concrete explanation alongside partial evidence.
        return {"blocker": decision.rationale or "The task is blocked.", "finished": True, "verified": False, "status": "Blocked"}
    # Freeze execution for legitimate human-only steps.
    if decision.kind == "assist":
        # Keep assistance explicit and resumable.
        return {"waiting": {"kind": decision.target if decision.target in {"login", "captcha"} else "assistance", "message": decision.rationale}, "status": "Waiting for user assistance"}
    # Apply task relevance only to actual supplied candidate URLs.
    if decision.kind == "queue_links":
        # A current queued page may be rejected only after its actual content was observed.
        if decision.target == "skip_current" and not state.get("link_batch"):
            # Require an actual queued destination, never an arbitrary unvisited-page deletion.
            frontier = list(state.get("frontier", []))
            # Bind rejection to this exact current main-page URL.
            current = urldefrag(state.get("observation", {}).get("url", ""))[0]
            # Reject malformed scope revisions through ordinary recovery.
            if state.get("link_batch") or not frontier or frontier[0] != current or decision.links or not decision.rationale.strip():
                # A different queued destination cannot be silently removed.
                return _failure("Queued-page review failed", ValueError("Reject only the current queued page with an explicit reason and empty links"))
            # Preserve the semantic exclusion without claiming source capture.
            history = [*state.get("history", []), {"decision":asdict(decision),"excluded_url":current,"success":True}]
            # Explain why this destination leaves the relevant frontier.
            _publish(state, "Skipped unrelated queued page: " + current)
            # Continue real destinations without marking the rejected page collected.
            return {"frontier":frontier[1:],"history":history,"last_outcome":{"success":True,"action":"queue_links"},"last_error":"","attempts":0,"candidate_finish":False}
        # Bind the reply to its concrete candidate batch.
        candidates = {item["url"] for item in state.get("link_batch", [])}
        # Reject invented destinations instead of silently crawling them.
        if any(url not in candidates for url in decision.links):
            # Grounding failures use the ordinary bounded recovery path.
            return _failure("Link review failed", ValueError("Selected URL was not in the supplied batch"))
        # Preserve previously queued relevant pages.
        frontier = list(state.get("frontier", []))
        # Queue selected URLs in original source order.
        for item in state.get("link_batch", []):
            # Avoid cycles and duplicate navigation requests.
            if item["url"] in decision.links and item["url"] not in frontier and item["url"] not in state.get("visited", []):
                # A new hostname still requires permission at execution time.
                frontier.append(item["url"])
        # Account for every reviewed candidate without dropping unreviewed batches.
        return {"frontier": frontier, "reviewed_links": [*state.get("reviewed_links", []), *candidates], "last_outcome": {"success": True, "action": "queue_links"}, "link_batch": [], "attempts": 0}
    # Preserve typed user conditions instead of retrying them as generic browser failures.
    try:
        # A finish proposal cannot skip deterministic source capture.
        if decision.kind in {"collect", "finish"}:
            # Identify the actual page supplying evidence.
            url = canonical_url(state.get("observation", {}).get("url", ""))
            # Check whether the finite goal or entity quota is already satisfied.
            goal_complete = bool(state.get("progress", {}).get("complete"))
            # A finish proposal or completed goal must never re-trigger collection if already satisfied.
            if goal_complete:
                # Do not collect if already complete.
                needs_collect = False
            # Check if finish proposal needs collection.
            elif decision.kind == "finish":
                # Only capture if no pages were ever collected, or this uncollected page is needed.
                needs_collect = not state.get("collected_pages") or (bool(url) and url not in state.get("collected_pages", {}) and not any(p.get("complete") for p in state.get("collected_pages", {}).values()))
            else:
                # Collect if unvisited, dirty, or requested scope differs.
                needs_collect = url not in state.get("collected_pages", {}) or state.get("collected_pages", {}).get(url, {}).get("dirty") or (decision.target or "body") != state.get("collected_pages", {}).get(url, {}).get("scope")
            # Collect an unvisited page before considering its result complete.
            updates = _collect(state, decision.target if decision.kind == "collect" else "body") if needs_collect else {}
            # An explicitly requested page is ready to finalize as soon as its finite capture returns.
            page_captured = _page_only_task(state.get("task", "")) and url in updates.get("collected_pages", state.get("collected_pages", {}))
            # A completed goal or satisfied collection report can verify immediately without extra cycles.
            progress_complete = bool(updates.get("progress", {}).get("complete")) or goal_complete or any(p.get("task_complete") for p in updates.get("collected_pages", {}).values())
            # Do not start another reasoning/link-review cycle after reaching this task's boundary or completing the goal.
            if page_captured or (progress_complete and updates):
                # Keep final verification distinct from continued scrolling or site exploration.
                _publish(state, "Requested goal reached; finalizing without extra cycles")
            # Ready to verify if page captured, goal completed, or finish proposal without pending collection.
            finish_ready = page_captured or progress_complete or (decision.kind == "finish" and not updates)
            # Broader website tasks preserve their existing relevant-link review behavior.
            updates.update({"candidate_finish": finish_ready, "last_outcome": {"success": True, "action": "collect"}, "status": "Checking source coverage", "last_error": ""})
            # Do not use the model's paraphrased output as the evidence body.
            return updates
        # Execute a single ordinary action through the selected transport.
        outcome = state["adapter"].execute(decision)
        # Tool-level failure is not successful progress.
        if outcome.get("success") is False:
            # Preserve the measured failure for strategy revision.
            raise RuntimeError("Browser action reported no verified progress")
    # A proposed host change requires explicit authorization.
    except AuthorizationRequired as exc:
        # Preserve the exact destination for resumption.
        return {"waiting": {"kind": "hostname", "url": exc.url}, "status": "Waiting for hostname authorization"}
    # Login, CAPTCHA, and potentially unbounded feeds have explicit waiting states.
    except AssistanceRequired as exc:
        # Freeze automatic actions until a concrete response arrives.
        return {"waiting": {"kind": exc.reason, **exc.details}, "status": "Waiting for " + exc.reason}
    # Cancellation is not a failed task attempt.
    except InterruptedError:
        # Preserve partial source data without a false success flag.
        return {"stopped": True, "finished": True, "verified": False, "status": "Stopped by user"}
    # Traversal/input errors must not be swallowed.
    except Exception as exc:
        # Retain specific diagnostics across graph channels.
        return _failure("Action failed", exc)
    # Preserve actual attempted input and backend evidence.
    history = [*state.get("history", []), {"decision": asdict(decision), "outcome": outcome, "success": True}]
    # Require independent post-action observation.
    return {"history": history, "last_outcome": outcome, "candidate_finish": False, "last_error": "", "observation_ready": False}


# Verify source-backed completion or the actual effect of an interaction.
def verify_node(state):
    """Reject unsupported answers and no-op actions; retain a reusable fresh observation."""
    # Keep verification cancellable.
    if _stopped(state):
        # Never verify an interrupted result.
        return {"stopped": True, "finished": True, "verified": False, "status": "Stopped by user"}
    # Reuse a matching final collection capture when no later action changed the page.
    try:
        # Collection already captured source, controls, geometry, and an immutable screenshot together.
        data = state["observation"] if state.get("observation_ready") and state.get("observation") else _observation_dict(state["adapter"].observe())
    # Do not send unauthorized content to the reasoning model.
    except AuthorizationRequired as exc:
        # Preserve a concrete waiting destination.
        return {"waiting": {"kind": "hostname", "url": exc.url}, "status": "Waiting for hostname authorization"}
    # Preserve ordinary observation failures for bounded recovery.
    except Exception as exc:
        # Return specific rather than generic diagnostics.
        return _failure("Verification failed", exc)
    # Keep immutable images without overwriting earlier browser states.
    screenshots = list(dict.fromkeys([*state.get("screenshots", []), *data.get("all_screenshots", [])]))
    # Finish proposals require independent source and scope evidence.
    if state.get("candidate_finish"):
        # Read measured coverage rather than a model confidence statement.
        pages = state.get("collected_pages", {})
        # Assemble content only from captured source records.
        output = state["store"].text(state.get("goal")) if state.get("store") is not None else state.get("output", "")
        # Optional model quotes must exist verbatim in actual evidence.
        quote = state.get("decision", {}).get("output", "")
        # Check whether finite goal completion is already established by measured progress.
        goal_complete = bool(state.get("progress", {}).get("complete"))
        # Determine if the task is in finite entity collection mode.
        finite_mode = state.get("goal", {}).get("mode") == "collect_entities"
        # For finite entity tasks, achieving the required record count satisfies coverage.
        # For broad crawling tasks, all visited pages must be complete.
        pages_complete = (goal_complete or any(page.get("task_complete") or page.get("complete") for page in pages.values())) if finite_mode else all(page.get("complete") for page in pages.values())
        # Require content, complete coverage, and an exhausted relevant frontier.
        valid = bool(output and pages and pages_complete and not state.get("frontier") and (not quote or quote in output))
        # Nonempty invented prose or incomplete traversal cannot verify.
        if not valid:
            # Retain partial information separately from the limitation.
            return {"finished": True, "verified": False, "output": output, "blocker": "Exact source evidence and complete traversal did not establish completion.", "status": "Partial or blocked"}
        # A finite entity goal is already proven by deterministic unique-record and constraint checks.
        finite_goal_complete = bool(finite_mode and goal_complete)
        # Broad or unbounded tasks still require a source-cited semantic objective assessment.
        if not finite_goal_complete and state.get("task") and state.get("store") is not None:
            # Keep semantic reasoning separate from deterministic source assembly.
            from models.base import audit_objective
            # Use the same selected model and current screenshot for this explicit audit.
            try:
                # Exact quotations must exist in the independently captured source store.
                objective_met, reason = audit_objective(state["provider"], state["task"], BrowserObservation(**data), state["store"].blocks())
            # Audit failures are explicit partial outcomes, never silent verification.
            except Exception as exc:
                # Preserve useful safe diagnostics without losing source evidence.
                objective_met, reason = False, "Objective audit failed: " + redact_secrets(str(exc))[:300]
            # Fidelity alone cannot establish that the correct subject was retrieved.
            if not objective_met:
                # Keep all exact collected material available for inspection.
                return {"finished": True, "verified": False, "output": output, "blocker": reason, "status": "Partial: objective not established"}
        # Publish a verified source-backed outcome.
        return {"observation": data, "screenshots": screenshots, "output": output, "finished": True, "verified": True, "status": "Completed with source and traversal evidence", "attempts": 0}
    # Check ordinary action effects against the prior actual page.
    previous = state.get("observation", {})
    # Determine which operation's effect is being verified.
    action = state.get("last_outcome", {}).get("action") or state.get("decision", {}).get("kind", "")
    # These operations have independent deterministic evidence.
    mechanical = action in {"collect", "queue_links", "wait", "scroll", "fill", "switch_tab", "close_tab"}
    # URL, text, or native-control state changes establish ordinary interaction progress.
    changed = data.get("url") != previous.get("url") or data.get("fingerprint") != previous.get("fingerprint") or data.get("text") != previous.get("text")
    # Do not reset retries merely because input transport returned normally.
    if not mechanical and not changed:
        # A subsequent fresh recovery observation can account for delayed UI updates.
        return _failure("Verification failed", RuntimeError("Action produced no observable UI change"))
    # A filter, tab, or pagination change at the same URL invalidates prior coverage.
    pages = dict(state.get("collected_pages", {}))
    # Preserve source already captured, but never treat its previous state as current.
    current_url = urldefrag(data.get("url", ""))[0]
    # Scroll-only and collection-induced viewport changes do not invalidate complete traversal.
    if changed and action in {"click", "fill", "press", "switch_tab"} and current_url in pages:
        # Require re-collection before the changed interface may finish successfully.
        pages[current_url] = {**pages[current_url], "dirty": True, "complete": False}
    # Reuse this fresh observation in the next decision cycle.
    return {"collected_pages": pages, "observation": data, "observation_ready": True, "screenshots": screenshots, "attempts": 0, "last_error": "", "candidate_finish": False, "status": "Verified action effect"}


# Count actual failed attempts without resetting on unverified model responses.
def recover_node(state):
    """Stop at five total failures and retain concrete diagnostics for strategy adaptation."""
    # Count the first actual failure as attempt one.
    attempts = int(state.get("attempts", 0)) + 1
    # Preserve the failure formerly lost through an undeclared state channel.
    error = state.get("last_error") or "Unclassified browser-agent failure"
    # Classify useful errors without exposing private SDK bodies.
    failure_type = "timeout" if "Timeout" in error else "action_failure"
    # Retain chronology and attempted actions for the selected model.
    history = [*state.get("history", []), {"decision": state.get("decision", {}), "error": error, "failure_type": failure_type, "success": False, "attempt": attempts}]
    # Publish meaningful live recovery status.
    _publish(state, f"Recovery {attempts}/{MAX_ATTEMPTS_PER_DECISION}: {error}", "WARNING")
    # Five failures exhaust this unresolved logical step.
    if attempts >= MAX_ATTEMPTS_PER_DECISION:
        # Retain partial evidence and a concrete blocker.
        return {"attempts": attempts, "history": history, "finished": True, "verified": False, "blocker": "Five attempts exhausted: " + error, "status": "Blocked after five failed attempts"}
    # Transient API failures wait in the worker, leaving UI and Stop responsive.
    delay = min(300.0, max(float(state.get("retry_delay", 0)), min(30.0, 2.0 ** attempts))) if state.get("retry_delay") else 0
    # Ordinary browser strategy errors do not incur quota cooldown.
    if delay:
        # Tell the user what is actually waiting instead of showing apparent activity.
        _publish(state, f"Provider cooldown: {delay:g}s before retry {attempts + 1}")
        # Live runs always supply the same cancellation event used by browser operations.
        event = state.get("stop_event")
        # Honor Stop immediately during the provider's cooldown.
        if event is not None and event.wait(delay):
            # Preserve source evidence while ending without another API call.
            return {"stopped": True, "finished": True, "verified": False, "status": "Stopped by user"}
    # A new cycle starts with a real observation and preserved error context.
    return {"attempts": attempts, "history": history, "last_error": error, "observation_ready": False, "candidate_finish": False, "status": "Recovering", "logs": [{"level": "ERROR", "message": error}]}
