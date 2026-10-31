# Intelligent Browser Agent — implementation and debugging plan

Prepared: 26 October 2026. Approved by the user on 26 October 2026 with the additional requirement for detailed file/function/line comments. Implementation and controlled validation are underway; live credentialed and user-site acceptance remain release gates.

Confirmed model configuration: Gemini uses `gemini-3.5-flash-lite`; Groq uses `qwen/qwen3.8-27b`. Each run uses only its selected model for screenshot understanding and DOM/accessibility-grounded reasoning. Do not combine models/providers or silently fall back. The user also has access to `openai/gpt-oss-120b`, but it is outside this release's fixed configuration because it cannot directly analyze screenshots. The fixed vision-capable models preserve the same task workflow across both provider choices.

The original planning copy was stored outside the project and no application changes were made during planning. This project copy records the approved plan; implementation followed the user's explicit approval. The five Markdown documents in `antigravity/` provide the baseline; the user's original requirements and subsequent answers refine that baseline. Conflicts are resolved in favor of the user's latest explicit decisions.

## 1. Agreed outcome and scope

Build a local Windows application with Streamlit and a shared LangGraph agent. The user searches for a website, explicitly chooses a suggestion, enters a natural-language task, and starts one selected browser method with one selected model provider. The agent observes screenshots and structured browser state, navigates accurately, traverses relevant interfaces and links, collects the requested information faithfully, and verifies its outcome.

| Decision | Agreed behavior |
|---|---|
| AI providers | Gemini and Groq, confirmed by the user. Correct the misleading Grok label and related identifiers; preserve the valid Groq endpoint while fixing its model and image requests. |
| Reasoning | One LangGraph agent owns task interpretation, decisions, verification, and recovery for all methods. Browser Use does not run a second autonomous agent. |
| Browser methods | Agent + Playwright MCP, Agent + Playwright CLI, and Browser Use; exactly one per run, with no silent substitution. |
| Observation | Screenshots plus DOM/accessibility data. Capture rendered UI content, not hidden application data or backend responses as a substitute for the UI. |
| Model controls | One fixed supported vision-capable model per provider, configured internally; no model-selection UI. |
| Fixed model configuration | Gemini: `gemini-3.5-flash-lite`. Groq: `qwen/qwen3.8-27b`. The selected model handles both screenshots and reasoning. Verify credentials, image input, structured output, and task behavior before calling either integration validated. GPT-OSS 120B is not included in this release or used as fallback. |
| Initial release | Information gathering, search, filters, sorting, extraction, and navigation. Purchases, messages, deletions, account creation, and other consequential workflows are outside this release. |
| Scope discovery | Automatically follow task-relevant links on the selected website. Track visited pages and explain exclusions or inaccessible content. |
| Website boundary | Stay on the exact selected hostname. Ask before moving to another hostname, including apex/www changes and sibling subdomains. Authorizations are explicit and scoped to the run. |
| Finite traversal | Open relevant expanders, tabs, and read-more controls; traverse finite pagination and load-more results. |
| Non-finite content | Ask for a stopping criterion when a feed or traversal has no clear finite end. Stopping at a chosen limit is labeled as bounded extraction. |
| Output | Preserve requested wording, values, labels, order, relationships, headings, lists, tables, code indentation, and meaningful spacing. Display in Streamlit and provide TXT/Markdown downloads. No default summarization. |
| Cursor | Passive in-browser indicator follows the exact resolved action target. Do not take control of the operating-system mouse. |
| Assistance | Pause and resume for login and CAPTCHA. Handle ordinary interruptions automatically. |
| Cookies | Use Reject all or necessary-only choices and disable optional categories. Necessary/login cookies remain allowed. Never silently accept optional cookies. |
| Website discovery | Actual web search without a model key; optional AI assistance for interpreting misspellings. Never fabricate domain suggestions to fill the list. |
| Acceptance | Controlled pages first. The user supplies real websites and exact tasks before final acceptance. |

Local sessions remain isolated by exact hostname and browser method. Headful/headless is a runtime setting, not another automation method. Downloading files from websites and processing those files remain outside the initial scope; downloading the application's own TXT/Markdown result is included.

## 2. Architecture and responsibilities

Streamlit owns configuration, explicit selection, task entry, live progress, human handoff, and results. A run supervisor owns one worker process per active run and communicates through commands and events. The worker owns the model client, browser adapter, LangGraph execution, and extraction services. This keeps browser/model work off the UI thread and provides a reliable cancellation boundary on Windows.

LangGraph will coordinate this workflow:

`interpret objective -> observe -> classify interruption -> plan next step -> validate target/action -> execute -> verify -> collect evidence/update traversal -> continue or finalize`

Conditional routes handle recovery, login, CAPTCHA, hostname authorization, non-finite scope decisions, manual stop, partial output, and blockers. Human handoff preserves the logical run and checkpoint; an already-visible browser stays available. A headless-to-headful transfer may require restarting the browser with its eligible session state. On resume, re-observe the actual browser state before taking another action.

Three services have distinct responsibilities:

1. The reasoning layer decides where to go and what task-relevant regions or links to inspect.
2. The browser layer executes concrete, validated actions through the selected method.
3. The evidence layer preserves captured UI content, ordering, relationships, and coverage. It assembles final extracted content without asking the model to rewrite it.

Small, task-focused observations may be supplied to the model for navigation. They are separate from the complete evidence store. Prompt-size limits must never silently truncate the final extraction.

Checkpoint state contains serializable run data and evidence references. Browser handles, API keys, provider instances, and subprocess objects stay in runtime context outside persisted graph state.

## 3. Shared contracts to implement

| Contract | Essential fields and behavior |
|---|---|
| Task specification | Original instruction, requested fields/regions, completion conditions, relevant-link policy, allowed exact hosts, initial-release action policy. |
| Observation | Observation ID, page/tab/frame identity, URL, screenshot ID, timestamp, CSS viewport, image dimensions, pixel ratio, scroll regions, current structured elements, and page-state fingerprint. |
| Element reference | Observation-bound identity, backend reference or stable locator, frame/shadow context, role/name, relevant ancestor context, bounding box, visible/enabled state, and resolution evidence. |
| Action request | Enumerated action, validated target, typed arguments, expected effect, originating observation ID, and logical step/problem ID. Scrolling includes container, direction, and distance. |
| Action result | Success/failure classification, actual target, before/after state, navigation/tab changes, duration, and normalized error. A returned dictionary alone is not success. |
| Captured block | Exact text, block type, section/row/cell relationships, source URL and UI state, ordered position, screenshot reference, and capture identity. |
| Traversal state | Pending/visited relevant pages, UI states, discovered containers, positions, collected record identities, expansion/pagination status, and stopping evidence. |
| Run outcome | Completed, waiting for user, stopped, partial, or blocked; separate fidelity/coverage checks, result artifact references, and unresolved limitations. |

No action may use an unknown reference, an ambiguous target, or an observation made stale by a relevant page change. Re-observe and resolve instead of guessing. Missing tab IDs must not default to tab zero.

## 4. Implementation phases and gates

Each change starts with a meaningful failing regression scenario, followed by a focused fix and the relevant tests. Preserve working components and public identifiers where practical. Update misleading tests rather than retaining assertions that approve false completion. Preserve the project's requested module/function documentation and explanatory executable-line comments.

### Phase 0 — establish a reproducible baseline

Work:

- Create a recoverable snapshot of source and configuration after approval, excluding credentials, browser profiles, and private runtime artifacts. The folder currently has no Git repository; do not assume Git rollback exists.
- Inventory the installed Python, Node, browser, CLI, MCP, Browser Use, LangGraph, Streamlit, and provider SDK versions.
- Establish dependency constraints/lock data from a validated combination. Remove runtime dependence on unpinned `@latest` installs.
- Add setup diagnostics for missing tools, browser binaries, invalid keys, permissions, and unsupported capabilities.
- Resolve the test temporary-directory permission issue without changing genuine browser sessions.
- Record current failure reproductions and phase timings. Do not turn failures into passing results by broadly swallowing exceptions.

Tests/gate: reproducible setup; a trustworthy test report; captured reproductions for premature finish, false verification, lost recovery detail, cursor/target mismatch, scroll return-type errors, extraction formatting loss, and monitoring errors. Existing evidence is 43 passing tests with four session tests blocked by temporary-directory permissions; this is not live-browser acceptance.

### Phase 1 — repair contracts, lifecycle, and immediate correctness defects

Work:

- Implement typed contracts and full graph state, including errors, outcomes, task criteria, traversal state, and evidence references.
- Remove the provider fallbacks that convert ordinary actions with empty output into finish.
- Remove blocked-to-success conversion and short-answer-to-whole-page replacement.
- Fix monitoring event serialization and unique run/screenshot IDs.
- Add worker ownership, event delivery, pause/stop commands, and terminal-state rules.
- Prevent overlapping runs, stale updates from an earlier run, and UI reruns from duplicating work.

Tests/gate: a valid click/fill/scroll remains that action on a long page; unrelated or invented output cannot verify; blockers remain blockers; typed events render; only one worker owns a run; failed action details survive a compiled-graph transition.

### Phase 2 — correct both model providers

Work:

- Correct the Grok/Groq naming in the UI, provider factory, configuration, and tests. Preserve the existing Groq endpoint `https://api.groq.com/openai/v1`; replace its fixed GPT-OSS model with `qwen/qwen3.8-27b` and add supported image inputs. Use `gemini-3.5-flash-lite` for Gemini.
- Use one fixed internal model ID per provider and show a read-only model caption if useful.
- Send matching screenshot/observation identifiers and the same action schema to both providers.
- Keep screenshot understanding and subsequent decisions on the selected model for the whole run. Respect each model's image and context limits by selecting current relevant screenshots; retain the complete evidence history separately. A provider capability failure is explicit and never triggers a cross-model handoff.
- Use supported structured output and validate responses, including target types, argument ranges, and permitted initial-release actions.
- Keep original task instructions distinct from untrusted website content. Replace contradictory extraction prompts.
- Implement explicit request timeouts, cancellation, bounded transient-error retries, and safe error messages. Invalid credentials and unavailable models are configuration blockers, not navigation-retry loops.
- Remove silent fallback to another model. Preflight selected-provider access when starting a run.

Tests/gate: both providers receive image evidence and return schema-valid decisions; malformed JSON, missing targets, image failures, unavailable models, authentication errors, timeouts, and rate limits have distinct outcomes. A live screenshot-based decision smoke test is required for each provider when keys are available.

### Phase 3 — make the three browser adapters genuinely compatible

Implement and validate adapters in sequence: MCP, CLI, then Browser Use. They must retain their selected execution method.

- MCP: pin the server version, inspect advertised tool schemas, normalize structured/readable results, add response deadlines and cancellation, consume useful diagnostics, correct wait units, and normalize screenshots/tabs/errors.
- CLI: pin the executable version, use an isolated persistent session, initialize artifact paths, parse actual command results, distinguish tool errors from process success, implement session save/load, and cancel owned subprocesses.
- Browser Use: use its supported element APIs and backend-node references instead of positional DOM indices and generic JavaScript clicks. Normalize string evaluation results and base64 screenshots. Keep one owned event-loop lifecycle and cancel outstanding operations cleanly.
- All adapters: implement observation, target resolution, click/fill/hover, scroll/measure, wait for a condition, relevant tabs/windows, scoped hostname authorization, screenshots, cancellation, session reuse, and cleanup through the same logical contract.
- Validate normal Windows headful launching before retaining or replacing desktop helpers. Replace the global low-level process monkeypatch with supported, narrowly scoped process launching where the launch tests establish it is unnecessary.

Tests/gate: the same controlled task executes in real browsers through each adapter in both visibility modes. Validate emitted browser events and resulting page state, not only method return values. An unsupported required capability blocks that adapter's compliance gate rather than causing a silent fallback.

### Phase 4 — accurate targets, clicks, cursor, and verification

Work:

- Bind targets to the current observation and resolve by actual backend identity or unique contextual locators.
- Handle duplicate labels, hidden controls, disabled targets, frames, open shadow roots, sticky overlays, and layout changes.
- Check visibility, readiness, and hit testing. Scroll the correct container to reveal the target; revalidate after movement or hover-driven changes.
- Use native browser input through each adapter's supported APIs. Avoid DOM `.click()` and direct `.value=` as a generic interaction strategy.
- Derive the cursor indicator and highlight from the exact same resolved target and input position. The indicator never searches page text, changes scroll position independently, or defaults to a guessed center.
- Match screenshot pixels to CSS coordinates explicitly when visual geometry is needed; recheck the target before input.
- Verify expected effects: correct destination, active filter state, entered search value, opened region, changed results, or measured scroll progress. For a no-op, do not reset retries as if progress occurred.

Tests/gate: decoy controls and duplicate labels never receive unintended input; stale references trigger re-observation; overlays are handled before clicking; cursor trace agrees with the browser event target across viewport sizes and pixel ratios; action success requires the expected page change.

### Phase 5 — efficient, complete traversal and relevant-link exploration

Work:

- Discover the page's real scroll containers and relevant content regions, including nested panels and permitted frame content.
- Traverse using measured, overlapping viewport-sized steps, capturing content before virtualized nodes disappear. Start at the relevant region's beginning when completeness requires it.
- Execute predictable scroll/collect/wait cycles locally without another model request for each mechanical scroll. Return to reasoning when a meaningful state change or choice requires it.
- Wait on content growth, loader disappearance, relevant DOM changes, and position stability with operation-specific deadlines. Do not rely on network idle alone or fixed sleep delays.
- Treat bottom detection as a candidate: perform multiple stability checks and check whether more content, pagination, expanders, or load-more controls remain.
- Maintain a task-relevant page frontier. Follow relevant links automatically, prioritize natural chapter/result ordering, track visited page/UI states, and avoid cycles. Preserve meaningful query parameters; do not merge distinct filtered pages indiscriminately.
- Enforce exact-host authorization for navigation, clicks, popups, and redirects with adapter-owned navigation controls. Test unexpected redirects as well as known link destinations. Ordinary third-party resource loading does not itself authorize browsing a new website.
- Recognize endless feeds or repeated state growth without an enumerable end, then request a user-defined stopping condition. Never call a chosen limit exhaustive completion.

Tests/gate: collect every expected block/record from long, delayed-load, nested-scroll, virtualized, expandable, paginated, and multi-page fixtures. Prove no records were missed or duplicated through overlapping captures. No arbitrary six-scroll cutoff. Unauthorized hostname transitions must not silently proceed.

### Phase 6 — faithful extraction, provenance, and result assembly

Work:

- Store captured UI blocks outside prompt-sized observations. Keep exact wording, Unicode, numeric formatting, labels, meaningful whitespace, and block relationships.
- Preserve heading hierarchy, ordered lists, paragraphs, table headers/rows/cells, and preformatted code. Collect relevant side panels and dialogs when requested; do not hard-code extraction to the first main/article element.
- Deduplicate repeated captures by source record/block identity and UI state. Never remove legitimate repeated wording or values merely because their text matches.
- For images/canvas or content with no trustworthy text representation, use visual transcription with explicit validation and uncertainty tracking. An uncertain transcription cannot receive the same exact-fidelity claim as validated rendered text.
- Track changing content as captured states with timestamps instead of silently merging incompatible values.
- Assemble the final content deterministically from captured evidence. Keep source URLs, coverage explanations, and limitations separate from the verbatim body.
- Render safely in Streamlit without interpreting captured content as executable HTML. Export UTF-8 TXT/Markdown; large results may be paged in the UI but remain complete in exports.
- Require separate checks for fidelity and coverage. Final completion needs both, together with satisfied task conditions. A model finish decision is only a proposal.

Tests/gate: expected captured text matches fixture ground truth exactly; code indentation, tables, special characters, order, and parent-child relationships survive capture and export; large output is not truncated; paraphrased or invented text is rejected; missing coverage produces partial/blocked status with available collected material.

### Phase 7 — complete Streamlit journey, discovery, and human handoff

Work:

- Trigger search on Search, not on every query change. Retrieve actual search results, interpret misspellings, validate candidates, deduplicate, and offer 3–5 relevant choices where available. Explain fewer results or search failure instead of inventing sites.
- Require explicit website selection before task execution. Keep a selected provider and browser method mutually exclusive using checkboxes; fade inactive alternatives while leaving switching possible. Disable changes during an active run.
- Keep masked Gemini and Groq key fields in the left sidebar, with only the selected field enabled. Use one headful/headless visibility toggle as the documents specify.
- Stream status, meaningful action logs, progressive extraction counts, and immutable screenshot history during execution. Starting another run clears the displayed previous run.
- Add Pause, Resume, Stop, and appropriate assistance/hostname/scope prompts. Automatically handle ordinary dialogs and cookie rejection. If access requires optional-cookie acceptance and no rejection path exists, preserve partial results and report that blocker; do not silently accept optional cookies.
- During login/CAPTCHA assistance, freeze agent input and preserve its checkpoint. In a headless run, transfer to a visible session using a validated adapter-specific procedure, preserve eligible session state, and verify the restored page before resuming. Some transient in-memory page state may require safe re-navigation; do not promise an unchanged browser process.
- After user assistance, re-observe and verify readiness. If headless transfer cannot preserve a usable state, report that clearly with partial results rather than pretending to resume.
- Expose session reuse and scoped clearing without mixing profiles from different hosts/methods.

Tests/gate: Streamlit interaction tests cover explicit selection, exclusivity/fading, key fields, Start validation, live events, stop, pause/resume, reruns, run reset, result exports, and partial results. Real adapter tests verify manual login/CAPTCHA handoff, session reuse, and headless-to-headful assistance.

### Phase 8 — performance, recovery, cancellation, and long-run reliability

Work:

- Profile observation, screenshots, tool/process calls, model requests, scrolling, extraction, and rendering separately. Report model/network latency separately from local traversal overhead.
- Reuse connections/processes and session state; avoid duplicate verify/observe captures when the same fresh observation can serve both.
- Remove artificial per-action delays and repeated cursor reinjection. Send selected screenshots/context to the model rather than retransmitting the entire capture history.
- Count at most five total failed attempts for the same logical problem, including the first attempt. Preserve the error and strategy history; reset only after evidence of real progress or a genuinely different problem.
- Detect repeated states and ineffective actions. Pause/report a blocker rather than retrying identical actions indefinitely.
- Check cancellation inside traversal and tool waits. Cancel model tasks, MCP reads, CLI processes, and Browser Use futures. Use graceful cleanup first and terminate only the owned worker/browser process tree if necessary.
- Replace the arbitrary 50-transition run cutoff with checkpointed execution cycles and progress checks. There is no fixed global task-duration limit; per-operation deadlines still apply.
- Bound UI memory and event rendering while retaining complete result artifacts. Keep credentials and authentication input out of persisted state and diagnostic output.

Tests/gate: Stop is acknowledged promptly and no new action starts afterward; active calls terminate or reach bounded cleanup; browser crashes and malformed tool results produce actionable outcomes; long valid runs survive many graph cycles; retry exhaustion is counted correctly; other user browser sessions are unaffected.

### Phase 9 — controlled acceptance, real-site validation, and delivery

Work:

- Run unit/contract tests, then real browser-adapter tests, then the full agent with real provider requests. Do not substitute mock adapters/providers for the final matrix.
- Exercise all 12 provider/method/visibility combinations on the core controlled journey.
- Repeat critical cursor, traversal, pause/resume, and cancellation scenarios to detect intermittent failures.
- Record sanitized logs, expected/actual captures, screenshots, action traces, coverage manifests, timings, model IDs, and runtime versions for failures and fixes.
- Once controlled gates pass, obtain the user's real website URLs, exact instructions, and expected results. Reproduce the originally reported behavior and validate the corrections against those tasks.
- Update README, setup instructions, validation status, architecture/state documentation, requirement traceability, and remaining limitations.

Tests/gate: the first release is not declared finally accepted until the user's real cases pass or an explicit limitation/scope adjustment is agreed. Missing keys, inaccessible sites, or unavailable acceptance tasks are documented as unexecuted gates, not counted as passed.

## 5. Core traversal algorithm

1. Interpret the requested information and establish task-relevant regions, pages, and expected result types.
2. Observe screenshot, URL, page/frame/tab identities, controls, containers, and current rendered content.
3. Resolve normal interruptions and reject optional cookies. Route login/CAPTCHA to human assistance.
4. Capture relevant content and its ordering/relationships before moving the viewport or changing a UI state.
5. Expand relevant controls and advance the relevant scroll container with overlap.
6. Await the content-specific readiness condition, measure progress, capture newly revealed content, and update evidence.
7. At apparent bottom, probe for delayed growth and remaining load-more/pagination/expansion actions. Repeat until a supported end condition exists.
8. Add newly discovered task-relevant links to the frontier, enforce exact-host authorization, and visit unprocessed relevant states in a predictable order.
9. Continue until the finite relevant frontier and required interface states are exhausted, the user supplies a non-finite stopping criterion, a blocker occurs, or Stop is requested.
10. Validate source fidelity and coverage separately; assemble verbatim results and label any incomplete or bounded scope explicitly.

Completeness is evidence-backed for the task scope and traversed/discovered interface. Arbitrary websites can conceal inaccessible content or change during collection; those cases require an explicit limitation instead of an unsupported universal completeness claim.

## 6. Practical verification scenarios

| Controlled scenario | Required observable result |
|---|---|
| Misspelled/ambiguous discovery | Correct intended host is offered using real search evidence; no invented filler domains. |
| Duplicate labels and decoy buttons | Only the intended contextual control receives input. |
| DOM replacement or moving target | Re-resolution occurs; stale target does not click a different element. |
| Sticky overlay and cookie manager | Optional cookies are rejected; underlying target is used only when actionable. |
| Different viewport/pixel ratio | Indicator and actual event target agree in CSS coordinates. |
| Long static page | Every expected section is retained after more than six scrolls. |
| Delayed lazy loading | Delayed records are captured before traversal completes. |
| Nested scrolling | The relevant panel reaches its end; outer-page movement is not mistaken for panel progress. |
| Virtualized rows | Rows removed from the DOM remain in the evidence store; overlapping captures do not duplicate records. |
| Tabs/accordions/read more | Relevant hidden states are opened, collected, and ordered. |
| Finite pagination and linked chapters | Relevant pages are visited once per meaningful state; chapter ordering and content are preserved. |
| Endless feed/navigation cycle | The agent asks for a limit or reports stalled progress instead of claiming exhaustive completion. |
| Tables/code/Unicode/repeated values | Exact text and meaningful structure survive display and TXT/Markdown export. |
| Large extraction | Complete artifact exceeds model observation limits without truncation. |
| False model finish or fabricated answer | Finalization is rejected without supporting source content and coverage. |
| Failed action or false-like tool result | Failure is normalized and verified; string False is not interpreted as success. |
| New tab, external link, and redirect | Correct tab is tracked; new-host authorization is required. |
| Login/CAPTCHA in both modes | Agent input pauses; assistance and re-observation resume the correct task. Synthetic CAPTCHA gates test handoff, not automated CAPTCHA solving. |
| Stop during each phase | No further action after stop acknowledgement; owned operations clean up and collected data remains available. |
| Worker/browser/API failure | Partial/blocked state retains diagnostics and collected evidence without false success. |
| Session reuse and UI reruns | Correct host/method session persists; reruns do not launch duplicate work. |

The 12 core matrix rows are: Gemini 3.5 Flash-Lite or Groq Qwen 3.8 27B x MCP, CLI, or Browser Use x headful or headless. The common deterministic adapter suite runs across every browser method; image-based decisions and the full controlled journey run through the actual selected provider/model for each matrix row.

## 7. Proposed measurable acceptance targets

These are release targets to measure on the user's computer, not results already achieved or fixed global execution limits.

- Controlled extraction fixtures: 100% expected relevant records/blocks, exact expected text, preserved relationships/order, and zero invented records.
- Controlled targeting fixtures: zero decoy clicks or unintended submissions across the prescribed repeated runs. Repeated success is evidence for the tested scenarios, not a guarantee on every future website.
- Navigation boundaries: zero silent unauthorized hostname transitions in the prescribed direct-link, redirect, and popup tests.
- Cursor trace: displayed resolved target and actual input event agree for every tested action.
- UI: live updates approximately every second while active; Stop acknowledgement within one refresh cycle under normal local load.
- Cancellation: target normal cleanup within five seconds after acknowledgement; forced termination is bounded and recorded, and profile integrity is checked afterward.
- Static traversal: zero model calls solely to decide the next predictable mechanical scroll. No artificial 0.6-second cursor pause per action. For a locally served static test, target local collect/scroll overhead below one second per viewport at the 95th percentile after warm-up, excluding startup and model calls.
- Dynamic traversal: wait as long as the documented readiness condition requires within its operation deadline; missed content cannot be traded for a faster success claim.
- Performance regression: compare baseline and corrected timings on identical controlled tasks, while requiring equal complete output. Any unmet target is reported and investigated rather than quietly relaxed.

## 8. Source changes expected after approval

Preserve the existing responsibility boundaries. Exact filenames may be refined during implementation, but the work is expected in these areas:

| Area | Planned work |
|---|---|
| `config/`, dependency files | Fixed model IDs, supported versions, operation limits, typed run settings, setup validation. |
| `domain/models.py`, `domain/contracts.py`, `domain/events.py` | Typed actions, observations, element references, evidence, coverage, outcomes, safe event serialization. |
| `models/` | Gemini 3.5 Flash-Lite and Groq Qwen 3.8 27B transports, accurate provider naming, image requests, strict responses, cancellation, error classification. |
| `browser/base.py` and the three adapters | Real shared capabilities, persistent sessions, correct result normalization, cancellation, exact-host controls. |
| `browser/observation_builder.py` | Separate compact navigation context from complete raw evidence; preserve geometry and identity. |
| `browser/cursor_init.js` | Passive event/target-driven indicator with no independent text targeting or scrolling. |
| `browser/session_manager.py`, `browser/tab_manager.py` | Exact-host isolation, real session save/load, live tab/frame identity and ownership. |
| `agent/state.py`, `agent/nodes.py`, `agent/graph.py`, recovery/validation/prompts | Correct persisted state, explicit objectives, verified effects, bounded retries, interrupts, safe finalization. |
| New traversal/extraction/evidence services | Relevant-link frontier, scroll collection, ordered block store, coverage validation and provenance. |
| `services/run_controller.py` and a dedicated worker module | Process lifecycle, commands/events, cancellation, cleanup, runtime-only secrets. |
| `services/website_discovery.py` | Actual keyless web search, supported normalization/typo assistance, failure handling without invented domains. |
| `services/monitoring.py`, `services/output.py`, `ui/view.py`, `app.py` | Responsive controls, live artifacts, assistance prompts, safe faithful rendering, complete exports. |
| `tests/unit`, `tests/integration`, `tests/e2e`, new controlled fixtures | Meaningful regression, browser-level, full-agent, fidelity, coverage, and performance tests. |
| `docs/` and README | Requirement mapping, supported setup, measured validation matrix, known limitations, operating guidance. |

Avoid unrelated rewrites. Keep changes reviewable by phase and preserve source snapshots. Session/profile migrations require their own validation so existing sign-ins are not casually destroyed.

## 9. Delivery milestones and approval boundary

| Milestone | Reviewable evidence |
|---|---|
| A: trustworthy vertical slice | A controlled task runs from Streamlit through one real provider and MCP, with correct action execution and honest verification. |
| B: method parity | The same action/observation contract works in MCP, CLI, and Browser Use, in both modes, without substitutions. |
| C: complete faithful extraction | Long, dynamic, nested, virtualized, and linked-page fixtures produce exact complete artifacts with coverage evidence. |
| D: operational reliability | Human handoff, exact-host authorization, sessions, Stop, reruns, and monitoring pass practical tests. |
| E: controlled release candidate | Full 12-combination matrix and performance/failure audit pass; documentation includes actual measured evidence. |
| F: user acceptance | User-provided real websites and exact tasks pass; material limitations are resolved or explicitly agreed. |

After approval, proceed phase by phase and report changed behavior, verification evidence, remaining failures, and the next gate. Approval of this plan authorizes implementation and its controlled verification; it does not mean the application is already correct. API keys will be supplied through masked application inputs, not embedded in source or requested in chat. Final acceptance remains pending the user's real test cases.

## 10. Provider references checked during planning

- [Gemini 3.5 Flash-Lite model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite): documented model with image input and structured output.
- [Groq Qwen 3.8 27B model documentation](https://console.groq.com/docs/model/qwen/qwen3.8-27b): documented image/text model, selected for the confirmed Groq provider.
- [Groq GPT-OSS 120B model documentation](https://console.groq.com/docs/model/openai/gpt-oss-120b): text-only input, so it cannot directly analyze screenshots.

Documentation establishes advertised capabilities, not access through a particular API key or successful browser-agent execution. Both require the implementation's live gates.
