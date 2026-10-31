"""Measured viewport traversal and exact rendered-block collection.

The collector executes predictable scrolling locally through the selected adapter.
It captures before moving, waits on content/loaders, discovers nested panels, and
records stable-end evidence. It never treats a screenshot count as completeness.
"""
# Allocate immutable viewport evidence filenames.
from uuid import uuid4
# Create stable detail-record identities from exact rendered source.
import hashlib
# Normalize immutable screenshot paths returned by batched browser operations.
from pathlib import Path
# Measure readiness deadlines and short quiet intervals.
import time
# Signal scope decisions without inventing an arbitrary completeness cutoff.
from domain.errors import AssistanceRequired
# Bind automatic region expansion to a fresh real browser observation.
from domain.models import AgentDecision
# Detect when a finite entity objective has enough unique qualifying source records.
from agent.goals import goal_records, relevant_expansion
# Remove recognized optional overlays before they block scrolling or exact source capture.
from services.interruptions import dismiss_observed_interruption, find_dismissible_interruption


# Dismiss one capture-observed interruption using a fresh action-bound observation.
def _dismiss_capture_interruption(adapter, capture, objective):
    """Return whether one supported overlay was dismissed from the current viewport."""
    # Avoid an extra screenshot/DOM request when the collection capture has no candidate.
    if find_dismissible_interruption(capture.get("elements", []), objective) is None:
        # The current source is unobstructed for this policy.
        return False
    # Bind native input to a current immutable observation and its exact DOM identity.
    observation = adapter.observe()
    # Reclassify the live interface because an overlay may disappear asynchronously.
    dismissed, _ = dismiss_observed_interruption(adapter, observation, objective)
    # Optional dismissal failure is non-fatal; the caller may still extract accessible source.
    return dismissed


# Wait for UI readiness after a scroll, honoring Stop during the entire operation.
def _settle(adapter, scope, container, bottom=False, advance=False):
    """Return a stable capture or fail explicitly when a relevant loader remains busy."""
    # Real executors batch movement, stable source, and screenshot where supported.
    if not bottom and hasattr(adapter, "capture_view"):
        # A CLI viewport takes one command instead of three separate launches.
        return adapter.capture_view(scope, container, advance)
    # Deterministic fake controllers preserve the same measured movement semantics.
    if advance:
        # The previous viewport is already committed before this movement begins.
        adapter.probe("scroll", target=container, direction="down")
    # Live adapters batch polling locally to avoid repeated CLI/RPC startup overhead.
    if hasattr(adapter, "settle"):
        # Explicit fake controllers retain the simpler fallback below for isolated tests.
        return adapter.settle(scope, container, bottom)
    # Use a longer grace period only at a candidate bottom where lazy growth may arrive.
    quiet = 1.0 if bottom else 0.12
    # Bound a single readiness wait without imposing a global task-duration limit.
    deadline = time.monotonic() + 10
    # Track the last relevant source/size state.
    previous = None
    # Require actual state stability instead of an unconditional animation delay.
    stable_since = time.monotonic()
    # Keep polling while the current readiness operation remains within its deadline.
    while time.monotonic() < deadline:
        # Stop cannot be hidden inside lazy-load waiting.
        adapter.check_cancelled()
        # Capture actual source blocks in the selected viewport.
        capture = adapter.probe("capture", scope=scope, container=container)
        # Measure the actual scroll range rather than inferring it from screenshots.
        metrics = adapter.probe("measure", target=container)
        # Compare source record identity and size, not the passive cursor.
        signature = (metrics["height"], metrics["top"], tuple((block["key"], block["text"]) for block in capture["blocks"]))
        # A changed DOM or scroll range restarts the quiet interval.
        if signature != previous:
            # Preserve the most recent meaningful state.
            previous = signature
            # Require a fresh stable interval after loading or recycling rows.
            stable_since = time.monotonic()
        # Return only after source stability and loader disappearance.
        if not capture["loading"] and time.monotonic() - stable_since >= quiet:
            # Preserve typed measurements as traversal evidence.
            return capture, metrics
        # Keep the wait cancellable rather than sleeping for seconds unconditionally.
        adapter.stop_event.wait(0.05)
    # A still-busy region is a partial result, not proof of completion.
    raise TimeoutError("Relevant content did not settle before the operation deadline")


# Scan a finite region and its nested containers without a fixed six-scroll cap.
def collect_page(adapter, scope="body", store=None, page_no=0, step_limit=None, goal=None, detail_region=False):
    """Collect exact visible blocks and report completeness, limits, links, and screenshots.

    Source evidence is committed before scrolling. An explicit step_limit produces
    bounded/partial output. Sustained unbounded growth asks the user for a criterion.
    """
    # Discard any collection observation belonging to a previous page or UI state.
    if hasattr(adapter, "_collection_observation"):
        # Only this traversal may publish its final matching screenshot/source pair.
        adapter._collection_observation = None
    # Explicit user bounds disable speculative multi-viewport capture beyond that bound.
    if step_limit is not None and hasattr(adapter, "_capture_batch_size"):
        # Preserve exact requested movement accounting for bounded extraction.
        adapter._capture_batch_size = 1
    # Preserve the original objective for task-relevance checks during interruption handling.
    objective = str((goal or {}).get("objective", ""))
    # Discover initial relevant containers without altering source output.
    first = adapter.probe("capture", scope=scope)
    # Dismiss a bounded stack of supported optional overlays before measuring containers.
    for _ in range(3):
        # Stop once no recognized interruption blocks the requested interface.
        if not _dismiss_capture_interruption(adapter, first, objective):
            # Preserve the first unobstructed capture for ordinary traversal setup.
            break
        # Re-read containers and source only after the native close click takes effect.
        first = adapter.probe("capture", scope=scope)
    # Read each discovered real scroll region in source order.
    container_ids = [item["id"] for item in first["containers"]]
    # An explicitly selected nested scroll panel is already the complete requested region.
    if scope not in {"body", "window", "main", "article", "[role=main]", "__iba_page_content__"} and scope in container_ids:
        # Traverse that panel and any nested child panels without slowly scrolling unrelated outer-page chrome.
        pending = [scope, *[item for item in container_ids if item not in {"window", scope}]]
    # A page/body or non-scrollable selected region still needs normal document traversal.
    else:
        # Begin with the outer document, followed by discovered nested panels.
        pending = container_ids
    # Avoid scanning a container twice when captures rediscover it.
    visited = set()
    # Retain viewport captures for callers without a durable store.
    blocks = {}
    # Preserve all real links discovered throughout lazy-loaded states.
    links = {}
    # Record immutable screenshots and per-container stopping evidence.
    screenshots = []
    # Keep supported limitations separate from complete source text.
    limitations = list(first["limitations"])
    # Track actual container reports for coverage verification.
    reports = []
    # Count movement for explicit user-bounded extractions only.
    steps = 0
    # Track inspected tab/expander identities without repeatedly toggling them closed.
    activated = {item["id_label"] for item in first.get("elements", []) if item.get("selected") == "true"}
    # Detect ineffective or cyclic load-more controls using actual source state.
    expansion_states = set()
    # Retain the actual final viewport for duplicate-free post-collection verification.
    last_capture = first
    # Repeatedly growing load-more results may have no finite endpoint.
    expansion_count = 0
    # A finite record objective stops traversal as soon as its measured predicate is met.
    goal_satisfied = False
    # Inspect all discovered relevant scroll containers.
    while pending:
        # Keep Stop responsive between container transitions.
        adapter.check_cancelled()
        # Preserve discovery order for deterministic output.
        container = pending.pop(0)
        # Repeated discovery of the same live panel is not a new region.
        if container in visited:
            # Continue to the next uninspected panel.
            continue
        # Mark the actual panel before any dynamic mutations can rediscover it.
        visited.add(container)
        # The initial outer document normally starts at zero and needs no extra CLI/RPC command.
        initial = next((item for item in first["containers"] if item["id"] == container), None)
        # Nested panels still need viewport restoration even when their own scrollTop is zero.
        if container != "window" or not initial or initial.get("top") != 0:
            # Reset the intended container to its start, revealing nested panels if needed.
            adapter.probe("reset", target=container)
        # Track repeated height growth to identify a potentially non-finite feed.
        growth_streak = 0
        # Establish the initial measured content height.
        previous_height = 0
        # Defer movement into the next viewport batch after committing the current source.
        advance = False
        # Preserve the previous measurement for stuck-container detection.
        previous_top = None
        # Continue until a supported end, user limit, or blocker occurs.
        while True:
            # Capture after local UI readiness without another model request per scroll.
            capture, metrics = _settle(adapter, scope, container, bottom=False, advance=advance)
            # A stuck panel must fail rather than loop through unchanged captures.
            if advance and metrics["top"] == previous_top and not metrics["bottom"]:
                # Preserve existing evidence and expose the concrete scrolling failure.
                raise RuntimeError("Scroll container made no progress before its bottom")
            # Expansion may change source without another scroll.
            advance = False
            # Preserve the newest actual source/screenshot pair for final verification reuse.
            last_capture = capture
            # A delayed optional overlay must be closed before it can block scrolling or pollute evidence.
            if _dismiss_capture_interruption(adapter, capture, objective):
                # Re-capture this same viewport after the real close action.
                advance = False
                # Do not commit obscured source or move the viewport yet.
                continue
            # Preserve source evidence before virtualized elements disappear.
            if store is not None:
                # Use stable page and region order rather than screenshot filename order.
                store.add(capture, scope, page_no, len(visited) - 1)
            # Retain all distinct source records for compatibility callers.
            for block in capture["blocks"]:
                # Do not collapse separate equal-valued records by text alone.
                blocks[(capture["url"], block["key"], block["text"])] = {**block, "url": capture["url"]}
            # A broad full-detail collection must not exhaust a listing that contains several matching cards.
            summary_goal = {**goal, "detail_level": "summary"} if goal and goal.get("detail_level") == "full" else None
            # Count compact qualifying entities only to recognize the wrong collection boundary.
            listing_records = goal_records(list(blocks.values()), summary_goal) if summary_goal else []
            # Stop before needless page traversal when the selected scope is demonstrably a multi-entity listing.
            if len(listing_records) >= 2 and scope in {"body", "window", "main", "article", "[role=main]", "__iba_page_content__"}:
                # Preserve captured cards for diagnostics but require the planner to open one entity detail.
                raise RuntimeError("Full-detail collection selected a multi-record listing; open one distinct entity detail region or page before collecting")
            # Queue links from every observed state, not just the initial viewport.
            for link in capture["links"]:
                # Preserve the first source ordering and label for each real destination.
                links.setdefault(link["url"], link)
            # Add newly revealed scroll panels to the same traversal frontier.
            for item in capture["containers"]:
                # Discover panels created only after loading or expansion.
                if item["id"] not in visited and item["id"] not in pending:
                    # Keep real region identity rather than replacing it with the window.
                    pending.append(item["id"])
            # Explicit bounds apply to repeated load-more input as well as scroll movement.
            if step_limit is not None and steps >= step_limit:
                # Keep source already committed while reporting bounded rather than exhaustive coverage.
                limitations.append("Explicit traversal-action limit reached")
                # No uninspected region can be claimed complete after the selected bound.
                pending.clear()
                # Leave this region without a false finite-end certificate.
                break
            # Count qualifying logical records before expanding unrelated interface controls.
            matching_records = goal_records(list(blocks.values()), goal)
            # A finite count is a task-completion boundary even when the page itself continues.
            goal_satisfied = bool(goal and goal.get("required_count") and len(matching_records) >= int(goal["required_count"]))
            # Publish task-level progress separately from lower-level scrolling telemetry.
            if adapter.monitor is not None and goal and goal.get("required_count"):
                # Cap the display at the requested count because surplus records are not part of the output contract.
                completed_records = min(len(matching_records), int(goal["required_count"]))
                # Name the logical entity so the user can see progress toward the requested result, not just page motion.
                adapter.monitor.update_status(f"Collected {completed_records}/{int(goal['required_count'])} qualifying {goal.get('entity', 'record')} records")
            # Inspect unopened relevant tabs/expanders only while more task evidence is needed.
            controls = [] if goal_satisfied else [item for item in capture.get("elements", []) if item.get("in_scope") and not item.get("disabled")]
            # Scope controls are actual observed elements, not guessed text matches on the page.
            expandable = next((item for item in controls if item["id_label"] not in activated and item.get("expanded") == "false" and relevant_expansion(item, goal)), None)
            # Repeat only genuinely repeatable result-loading controls at a measured bottom.
            more = next((item for item in controls if item.get("tag") == "BUTTON" and item.get("text", "").strip().lower() in {"load more", "load more results", "show more results"}), None) if metrics["bottom"] else None
            # Finite button pagination requires actual pagination context or an explicit page label.
            next_page = next((item for item in controls if item.get("tag") == "BUTTON" and (item.get("text", "").strip().lower() == "next page" or (item.get("pagination") and item.get("text", "").strip().lower() in {"next", "›", "»", ">"}))), None) if metrics["bottom"] else None
            # Finish the current tab's finite pages before replacing it with another tab.
            next_tab = next((item for item in controls if item["id_label"] not in activated and item.get("role") == "tab" and item.get("selected") == "false"), None) if metrics["bottom"] else None
            # Expand in place, exhaust finite results, then switch to an unvisited tab.
            control = expandable or more or next_page or next_tab
            # Capture evidence before any expansion replaces its current visible content.
            if control is not None:
                # A load-more control that keeps adding results requires an explicit user bound.
                if control is more and expansion_count >= 20 and step_limit is None:
                    # Preserve current exact source before asking for a stopping criterion.
                    raise AssistanceRequired("scope_limit", {"message": "Load-more results keep growing. Enter a maximum total traversal-action count for this page.", "scope": scope})
                # Count repeated expansion input independently of ordinary finite tab changes.
                expansion_count += int(control is more)
                # Detect a control that cycles through an already captured UI state.
                signature = (control["id_label"], capture["text"], metrics["height"])
                # Repeated state cannot establish useful traversal progress.
                if signature in expansion_states:
                    # Preserve source data and report the concrete blocker.
                    raise RuntimeError("Expansion control repeated an already visited UI state")
                # Retain the state before dispatching input.
                expansion_states.add(signature)
                # Bind this input to a fresh observation rather than the collector's older screenshot.
                current = adapter.observe()
                # Use the same native target and cursor path as ordinary agent clicks.
                adapter.execute(AgentDecision(kind="click", target=control["id_label"], observation_id=current.observation_id))
                # Never repeatedly close/reopen an already inspected expander or tab.
                activated.add(control["id_label"])
                # Include actual expansion input in any explicitly bounded traversal.
                steps += 1
                # Replaced tab/page content must be traversed from its beginning.
                if control.get("role") == "tab" or control is next_page:
                    # Native clicks may retain an old bottom offset on the new content.
                    adapter.probe("reset", target=container)
                    # Previously scanned nested regions need fresh traversal in this state.
                    pending = [item["id"] for item in adapter.probe("capture", scope=scope)["containers"] if item["id"] != container]
                    # Keep the active container visited while refreshing changed nested panels.
                    visited = {container}
                # Recollect actual new UI content before moving the viewport.
                continue
            # Throttle screenshots: capture on initial view, milestones, or goal satisfaction.
            should_save_shot = (steps == 0) or (steps % 10 == 0) or goal_satisfied
            # Check if this step should write a screenshot.
            if should_save_shot:
                # Preserve viewport image evidence without repeatedly overwriting a latest file.
                adapter._screenshot_dir.mkdir(parents=True, exist_ok=True)
                # Allocate an immutable absolute image path.
                path = Path(capture["screenshot_path"]) if capture.get("screenshot_path") else adapter._screenshot_dir / ("collect_" + uuid4().hex + ".png")
                # Use the selected adapter's actual screenshot transport.
                if not capture.get("screenshot_path"):
                    # Injected controllers may retain a separate screenshot transport.
                    adapter._screenshot(path)
                # Retain a direct path to the captured viewport.
                screenshots.append(str(path))
                # Publish screenshots and counts during the run.
                if adapter.monitor is not None:
                    # The UI need not wait until graph completion for image history.
                    adapter.monitor.add_screenshot(str(path))
            # Publish concise progress during the run.
            if adapter.monitor is not None:
                # Keep progress grounded in actual captured records.
                adapter.monitor.update_status(f"Collecting {capture['url']}: {len(blocks)} blocks, {steps} scrolls")
            # Stop immediately after the requested number of validated unique records exists.
            if goal_satisfied:
                # Record a task-bounded completion certificate separately from document bottom.
                reports.append({"container": container, "bottom": metrics["bottom"], "height": metrics["height"], "top": metrics["top"], "stable": True, "goal_satisfied": True})
                # No additional panels are needed for this finite objective.
                pending.clear()
                # Leave the current traversal loop without capturing unrelated page chrome.
                break
            # Check explicit bounds without mislabeling bounded data as exhaustive.
            if step_limit is not None and steps >= step_limit:
                # Keep completed evidence available while clearly reporting the limit.
                limitations.append("Explicit scroll limit reached")
                # Return partial coverage through the ordinary report path.
                pending.clear()
                # Leave this container without a complete stopping certificate.
                break
            # Verify an apparent bottom after a longer delayed-growth grace interval.
            if metrics["bottom"]:
                # Batched Playwright capture may already include delayed-growth verification and its screenshot.
                if capture.get("stable_bottom"):
                    # Reuse the exact capture that followed the full bottom grace interval.
                    final_capture, final_metrics = capture, metrics
                # Other transports still require the normal explicit final grace check.
                else:
                    # A delayed loader may reveal a larger document after the first bottom measurement.
                    final_capture, final_metrics = _settle(adapter, scope, container, bottom=True)
                # Preserve final-grace records and links in nonpersistent reports as well.
                for block in final_capture["blocks"]:
                    # Keep legitimate repeated values separate through actual source identity.
                    blocks[(final_capture["url"], block["key"], block["text"])] = block
                # Late-loaded pagination/chapters still need task-relevance review.
                for link in final_capture["links"]:
                    # Preserve the first observed source label/order.
                    links.setdefault(link["url"], link)
                # Commit any content revealed during the bottom grace period.
                if store is not None:
                    # Preserve late-loaded records before considering completion.
                    store.add(final_capture, scope, page_no, len(visited) - 1)
                # The grace-period capture is the actual newest state at this page position.
                last_capture = final_capture
                # Only stable size and an actual bottom establish a finite stopping condition.
                if final_metrics["bottom"] and final_metrics["height"] == metrics["height"]:
                    # Record measured end evidence rather than a model completion assertion.
                    reports.append({"container": container, "bottom": True, "height": final_metrics["height"], "top": final_metrics["top"], "stable": True})
                    # Continue to remaining nested panels.
                    break
            # Detect sustained growth rather than imposing a hidden finite scroll count.
            growth_streak = growth_streak + 1 if metrics["height"] > previous_height and previous_height else 0
            # Update measured height for the next content-growth comparison.
            previous_height = metrics["height"]
            # A continuously expanding feed needs an explicit stopping criterion.
            if growth_streak >= 20 and step_limit is None:
                # Preserve data before pausing for a scope decision.
                raise AssistanceRequired("scope_limit", {"message": "Content keeps growing. Enter a maximum total traversal-action count for this page.", "scope": scope})
            # Preserve the current position before the next atomic viewport batch.
            previous_top = metrics["top"]
            # The next batch advances only after this source capture was committed.
            advance = True
            # Count actual requested traversal movements independently of model decisions.
            steps += 1
    # Full-detail collection groups one explicitly scoped expanded interface or detail page as one logical record.
    if goal and goal.get("detail_level") == "full" and (detail_region or scope not in {"body", "window", "main", "article", "[role=main]", "__iba_page_content__"}):
        # Preserve unique rendered blocks in their captured source order.
        detail_parts = [block["text"] for block in blocks.values() if str(block.get("text", "")).strip()]
        # Join only block boundaries; never summarize or rewrite source wording.
        detail_text = "\n\n".join(detail_parts)
        # Require substantial per-entity source so a title/card cannot masquerade as complete detail.
        # Confirm this region is not another multi-record listing before creating one completed detail record.
        summary_goal = {**goal, "detail_level": "summary"}
        # Multiple qualifying record containers prove this is a listing rather than one entity's complete information.
        listing_records = goal_records(list(blocks.values()), summary_goal)
        # Require substantial source and a single-entity boundary.
        if len(detail_text) >= 200 and len(listing_records) < 2:
            # A dedicated detail page has a stable entity URL, while a shared panel needs its exact state hash.
            detail_identity = "detail-url:" + first["url"] if scope == "__iba_page_content__" else "detail:" + hashlib.sha256(detail_text.encode("utf-8")).hexdigest()
            # Retain one complete exact record while leaving its component blocks auditable.
            detail_block = {"key": detail_identity, "stable_path": detail_identity, "entity_key": detail_identity, "entity_url": "", "persistent": False, "kind": "record", "text": detail_text, "y": 0, "x": 0, "headings": [], "detail_complete": True}
            # Add the aggregate to compatibility output and task progress exactly once.
            blocks[(first["url"], detail_identity, detail_text)] = detail_block
            # Persist the exact aggregate through the normal durable evidence path.
            if store is not None:
                # Reuse current capture provenance while storing only the aggregate record.
                store.add({**last_capture, "blocks": [detail_block]}, scope, page_no, len(visited))
            # Recompute completion across every previously stored entity plus this new record.
            completion_blocks = store.blocks() if store is not None else list(blocks.values())
            # A multi-entity detail task completes only after the durable global evidence reaches its count.
            goal_satisfied = bool(goal.get("required_count") and len(goal_records(completion_blocks, goal)) >= int(goal["required_count"]))
    # Publish the final current browser evidence without repeating the same screenshot and DOM read.
    if hasattr(adapter, "remember_collection_capture"):
        # The adapter validates that the matching immutable screenshot exists.
        adapter.remember_collection_capture(last_capture)
    # A limitation prevents an unsupported exhaustive-completion claim.
    complete = goal_satisfied or not limitations and len(reports) == len(visited)
    # Return exact content and concrete stopping evidence separately.
    report = {"url": first["url"], "scope": scope, "complete": complete, "task_complete": goal_satisfied, "traversal_complete": not limitations and len(reports) == len(visited) and all(item.get("bottom") for item in reports), "containers": reports, "limitations": limitations, "blocks": list(blocks.values()), "links": list(links.values()), "screenshots": screenshots, "scrolls": steps}
    # Persist coverage independently from final-answer wording.
    if store is not None:
        # Avoid duplicating raw blocks in the compact page coverage table.
        store.page(first["url"], {key: value for key, value in report.items() if key not in {"blocks", "links", "screenshots"}}, page_no)
    # Let the graph classify relevant links and verify the task against evidence.
    return report
