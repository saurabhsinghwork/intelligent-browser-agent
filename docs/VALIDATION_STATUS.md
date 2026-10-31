# Validation status — 26 October 2026

Status: implemented local candidate with controlled real-browser validation. Live credentialed model runs and the user's real-site acceptance remain outstanding. This record replaces the earlier statement that dependencies and real browser testing were unavailable.

## Automated checks

Maintained unit test suite: `python -m pytest tests/unit/` — **108 passed**.

The suite verifies:
- Multi-provider vision models (Gemini 3.5 Flash-Lite and Groq Qwen 3.8 27B) with strict JSON schema and multimodal image payloads.
- Master-detail LinkedIn extraction strategy (`agent/strategies/linkedin.py`): card discovery, detail extraction, resumption from prior store, and high-speed batch evaluation parsing.
- Browser Use intent management (`browser/browser_use.py`): exact-host authorization, CDP paused document interception, internal scheme pass-through (`chrome-error:`, `chrome:`, `about:`, `data:`), and async evaluate promise unwrapping.
- Finite goal completion verification (`agent/nodes.py`): multi-cycle entity goal completion acceptance without requiring full link frontier exhaustion.
- Evidence recording & SQLite storage: exact original text retention, block hierarchy, and markdown/manifest generation.
- Real browser transport contracts across Playwright MCP, Playwright CLI, and Browser Use.

Production documentation audit: `python -B tools/check_comments.py` returned `{}`: no missing module/class/function descriptions or explanations for executable production statements were found.

The application runs locally on `http://localhost:8502`.

## Real browser checks completed

Every PASS below used the actual selected executor and local HTTP fixtures. Browser diagnostics did not use provider keys. The worker tests use a deterministic model collaborator while retaining the real process supervisor, LangGraph, browser, collector, and evidence store.

| Controlled behavior | Playwright MCP | Playwright CLI | Browser Use |
|---|---|---|---|
| Native fill and intended duplicate-label click | PASS | PASS | PASS |
| Actual headful pointer remains on resolved target | PASS | PASS | PASS |
| 60 long-page records, 60 nested table rows, exact code whitespace | PASS | PASS | PASS |
| 24 delayed records and 80 recreated virtual rows | PASS | PASS | PASS |
| 48 tab/page records, finite load-more and expansion | PASS | PASS | PASS |
| Trusted native click inside open shadow DOM | PASS | PASS | PASS |
| Block unapproved ordinary link, redirect, and script popup before trap-server request | PASS | PASS | PASS |
| Explicit hostname grant permits the requested destination | PASS | PASS | PASS |
| Headless -> visible synthetic assistance -> headless, authenticated cookie retained | PASS | PASS | PASS |
| Spawned worker follows two relevant chapters without backlink loop; exact source once | PASS | PASS | PASS |
| Stop during a blocked simulated model call; no surviving profile-owned browser | PASS | PASS | PASS |

The assistance fixture simulates a person's Continue click; it does not solve a real CAPTCHA or use credentials. Ordinary lifecycle output included Browser Use shutdown warnings and local HTTP connection-reset messages during forced browser termination. Those messages were not counted as evidence of failure or success; source, actual session state, process ownership, and assertions determined the results.

## Measured traversal observations

These are local fixture observations rather than universal performance claims. No model request was made per mechanical scroll.

| Dynamic fixture: 24 lazy records + 80 virtual rows | Observed collection time |
|---|---|
| CLI before transport batching | 79.89 seconds |
| CLI after transport batching | 41.58 seconds |
| MCP before transport batching | 28.34 seconds |
| MCP after transport batching | 19.31 seconds |
| Browser Use | 9.14 seconds |

Different runs may use slightly different overlapping scroll counts because loading timing changes page height. All runs compared complete expected logical records, not a plausible text length.

Real keyless discovery of `flikart` returned five actual suggestions, including `https://www.flipkart.com/`, after replacing obsolete `duckduckgo_search` with maintained `ddgs==9.16.1`. Discovery did not require an AI model key and did not invent replacement domains.

## Inspectable evidence examples

All paths are relative to the project root; full source, Markdown, and raw provenance are retained in each named run directory.

| Scenario | Run artifact directory |
|---|---|
| MCP optimized dynamic extraction | `data/run_artifacts/916231d7fa8941059b58ffc433b8ba7c/` |
| CLI optimized dynamic extraction | `data/run_artifacts/80d708ed73ce4daeb8f633f8fda521ce/` |
| Browser Use dynamic extraction | `data/run_artifacts/a6c14c2faf63497eb5e7d8d83bd654f0/` |
| MCP tabs, pagination, load-more, shadow input | `data/run_artifacts/0661633f0cbf42f1b3919c11c90c93eb/` |
| CLI tabs, pagination, load-more, shadow input | `data/run_artifacts/e6f9c27aaea7425aaaa5e6c4543c888d/` |
| Browser Use tabs, pagination, load-more, shadow input | `data/run_artifacts/e0ff4acf22c046248de99bf0a9175b99/` |
| MCP real two-page worker/graph | `data/run_artifacts/80e9fbb5cf124692b6368e97bd15b213/` |
| CLI real two-page worker/graph | `data/run_artifacts/5331297b05f2436f84061dde5cd36c39/` |
| Browser Use real two-page worker/graph | `data/run_artifacts/15d0b3e46f7c4473b8f91d98f6c07c70/` |
| MCP Stop with independent browser-process audit | `data/run_artifacts/140f3461c931444f88ff29922cfb0c33/` |
| CLI Stop with independent browser-process audit | `data/run_artifacts/3ba1f670464e4464b107a588a4fce87c/` |
| Browser Use Stop with independent browser-process audit | `data/run_artifacts/24c48c20e85d4af8a0b86e0a81181daa/` |

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -B tools/check_comments.py
.\.venv\Scripts\python.exe -B tests/browser_smoke.py mcp --headed --collect
.\.venv\Scripts\python.exe -B tests/browser_dynamic.py playwright_cli
.\.venv\Scripts\python.exe -B tests/browser_interactive.py browser_use
.\.venv\Scripts\python.exe -B tests/browser_policy.py playwright_mcp
.\.venv\Scripts\python.exe -B tests/browser_handoff.py playwright_cli
.\.venv\Scripts\python.exe -B tests/worker_smoke.py browser_use
.\.venv\Scripts\python.exe -B tests/worker_smoke.py playwright_cli --stop
```

Replace the method argument with the other actual executor to repeat its corresponding diagnostic. `browser_smoke.py` accepts the shorter `mcp` and `cli` aliases. Other diagnostics use the full configured identifiers. Tests use private loopback HTTP ports and isolated method/origin profiles.

## Outstanding release gates and limitations

1. Enter a valid selected-provider key in the application's masked sidebar field. No real provider key was used during this implementation.
2. Verify actual Gemini `gemini-3.5-flash-lite` and Groq `qwen/qwen3.8-27b` image input, structured output, quotas, objective selection, and reasoning. Official model capability documentation was checked; account access and actual task quality were not inferred from that documentation.
3. Run all six provider/method combinations in both visibility modes with real model calls. The passing browser matrix is not this credentialed twelve-combination matrix.
4. The user supplies real websites and exact tasks before final acceptance. Compare requested source wording, all finite records, links, UI relationships, and outcome against the actual site.
5. Embedded frames in the requested extraction scope currently prevent complete coverage; frame-aware extraction remains incomplete. Relevant canvas data is reported as requiring verified visual transcription. Image-only or closed-shadow content does not have verified exact transcription support.
6. Unusual pagination labels, accessibility-poor layouts, loaders without observable signals, and content delayed beyond the current stable-bottom window may require additional site-specific work. Browser restart assistance cannot preserve arbitrary JavaScript memory or every IndexedDB-dependent flow.
7. Markdown is a structural companion; exact internal text and complete cell/span/provenance metadata live in TXT and the manifest. Arbitrary pixel layout is not reproduced by a text download.

No unsupported extraction case or unperformed live model run is claimed as passed.

## Visible-window regression fix following the user's log

The user supplied a run with `headful=True` but no visible window. Prior checks proved
native browser actions and pointer coordinates; they did not independently prove
placement on the user's displayed Windows desktop.

Headed Windows launches now use an owned native `CreateProcessW` helper with an
explicit input-desktop destination. Python's ordinary `subprocess.STARTUPINFO`
does not forward `lpDesktop`; assigning that Python attribute is insufficient.
No global process-creation monkeypatch or desktop switch is used.

Startup verifies the actual profile-owned native browser frame on the input
desktop and stops with a concrete error if it cannot be shown. The passive marker
is initialized through a real browser mouse event before model reasoning, including
collection-only tasks. Short native trajectories end at the resolved click target.
The visibility toggle now has an explicit persistent Streamlit key.

Practical reproduction: `tests/browser_visible_desktop.py` creates a private host
desktop without switching the person's screen, launches the actual selected
executor there, and asserts that its native browser frame appears on the displayed
desktop, that the cursor is visible before task clicks, and that normal cleanup
closes the real window. **MCP, CLI, and Browser Use all passed.**

Native headful fill/click/cursor alignment tests also passed after the change.
The updated automated suite passed **68 tests in 20.45 seconds**.
The supplied Gemini 503/504 responses are separate provider availability/deadline
failures; this window fix does not claim to eliminate those service responses.


## 2026-10-27 demo repairs and observed limits

- The user's credentialed Gemini/MCP run (1036e87069ad4508abf61fea15b20621) reproduced a real stuck nested scroll panel. It ended blocked after five attempts; that run is not a success. Its instruction was 'details of python operator', rather than the explicit single-page diagnostic task.
- Cursor rendering now uses a red Windows-style SVG arrow with its tip at the actual native mouse coordinates. Actual headful wheel input moves the pointer into the resolved content/panel. The operating-system mouse stays independent.
- Wheel dispatch is checked against actual panel movement. When native wheel input is intercepted, trusted code scrolls only the same already-resolved container and checks its rendered result. The collector still rejects a genuinely immovable, unfinished panel.
- Nested panel reset restores the outer-document position where the panel was discovered, preventing footer-dependent fixed sidebars from being traversed with a collapsed viewport.
- Browser Use now uses installed Google Chrome. Its managed profile name prevents browser-use 0.11.13 from silently copying that profile into a temporary directory, keeping visibility checks and process ownership aligned. Existing older profile folders are retained.
- Headed controlled CLI and Browser Use each passed actual fill, intended click, cursor alignment, 60 records, 60 table rows, and finite collection. Browser Use cleanup emits library focus-recovery warnings after Chrome closes; the diagnostic still exited successfully.
- Real W3Schools explicit-page diagnostics: MCP headless passed (4 scrolls, 1 container); CLI headful passed (6 scrolls, 1 container, 55.52 seconds for collection/finalization). These diagnostics use real browser/source evidence but bypass paid model reasoning.
- Deliberately blocked native wheel events on the real full-body W3Schools page: MCP reached stable bottoms for both containers after 59 scrolls, before the additional outer-position restoration refinement. Full-body extraction correctly remained partial because embedded frames were uninspected.
- The maintained automated suite passed 77 tests. Restricted execution emitted a Python temporary-directory cleanup PermissionError after the tests; this was not a test assertion failure. Production comment audit returned an empty finding list.
- The local Streamlit health endpoint at http://127.0.0.1:8512/_stcore/health returns ok. CLI/MCP services start on demand for the chosen run rather than running all three executors together.

The computer-use skill could read the user's normal Chrome accessibility controls, but screenshots timed out and coordinate input failed. The user started the credentialed run manually; a fresh CLI run was requested after the fixes. Credentialed end-to-end acceptance remains pending until that new run succeeds. The complete provider/method/visibility matrix and unsupported-frame/image/canvas cases above remain release gates.

Additional verification: after outer-position restoration, the same deliberately wheel-blocked real MCP page reached both stable container bottoms in **13 scrolls**, down from 59. Artifacts: data/run_artifacts/2fb342ad309a4b778e84ac1ca7bc3516. Its frame limitations remained correctly partial. A later repeat CLI cursor diagnostic lost its browser session before a scroll probe ('Browser ... is not open'); earlier successful headed cursor/collection tests are retained, but this repeat is not recorded as passed. No fresh credentialed run event was present after the user's second Start report; app-state clarification is pending.

The repeat headed CLI cursor check then passed (affb45fb289a4e409a9cfcae25013ff7): actual native fill, correct duplicate-button click, arrow-tip alignment with the target bounds, and real scrolling. A fresh credentialed user CLI run df2dde99a3344a17a6a54f6548c9251d appeared and verified its visible browser before model reasoning.

Live Gemini/CLI run findings: the user entered 'all python operator details from that site' on the Python homepage. The model twice proposed an absent element ID; the executor rejected both before input, then the run navigated correctly. It also requested a nonexistent semantic main selector before recovering to body collection. Follow-up repairs rank task-bearing control labels/URLs within the bounded provider context, include exact observed target alternatives in invalid-ID feedback, and resolve semantic main/article requests through actual landmarks and common main-content IDs. The real run collected the operators page through 19 movements and advanced to relevant-link review, with no stuck-scroll recovery. Its site-wide task permits continued relevant-page exploration. The expanded maintained suite passed **78 tests**; the comment audit remains empty.

The live site-wide run then exposed a separate frontier bounce: a generic homepage was queued, and the model repeatedly returned to the already collected operators page. The user stopped that run; it is not a successful end-to-end acceptance. Follow-up fixes add explicit observed-page rejection (queue_links / skip_current with a recorded rationale), task-context guidance against generic home/logo links, and evidence-aware cross-page cycle detection. New source, reviewed links, or a changed relevant frontier resets the guard; URL changes alone do not. A practical real Chrome/MCP/LangGraph diagnostic terminated the deliberately bouncing workflow after six navigations with an honest partial result. The full suite passed **81 tests**, and the final focused regressions passed 11 tests; production comments audit returned {}. A fresh credentialed run is required to validate the updated model behavior.

Final link-review regression: the live model used target skip_current when declining a whole link batch. Batch selection now takes precedence over the spare target field, and link-only provider schemas constrain target to an empty string. A real spawned MCP browser worker using that exact noisy response shape completed both chapters with verified exact source and traversal evidence (67e981952e22484baa08bab76b18c8bc). Full suite: **82 passed**; comments audit: {}. The latest credentialed run 34870f0a746e4cf285371836ace76262 is confirmed to contain the exact prepared single-page instruction.

Final credentialed single-page demo: 34870f0a746e4cf285371836ace76262 used the exact prepared instruction in the user's installed, visible Chrome via CLI. It performed the intended navigation without action errors, captured **40 source blocks**, traversed **6 scrolls**, logged 'Requested page captured; finalizing without following other pages', and terminated. It did not start link-review crawling. Its result is **partial/unverified**, not verified completion: the requested region contains about:blank frames with rendered SVGs. The frame diagnostic confirmed accessible complete documents with empty visible text and unlabeled rendered SVG content. Those frames were not silently discarded, and their visual information has no verified extraction support yet. Exact text/Markdown/manifest exports remain available in that run folder. The Streamlit service remains healthy on port 8512.



### 2026-10-27 — Styled code-block fidelity repair and final regression evidence

The W3Schools Python Operators export exposed a source-fidelity defect after the bounded live Chrome demo: styled code containers such as `.w3-code` use inline syntax-highlighting spans, so the collector emitted individual tokens on separate lines instead of preserving the rendered code line.

The page probe now treats `pre`, `.w3-code`, `.code-block`, and `[role="code"]` as complete rendered code blocks. It also groups visible inline-only child runs through the parent element's rendered `innerText`, while continuing to traverse shadow roots independently. This preserves displayed spacing and line breaks without asking the model to reconstruct or summarize source content.

Real-browser validation after the repair:

- Playwright MCP captured the real W3Schools Python Operators page in four scroll steps and one stable scroll container.
- Corrected artifact: `data/run_artifacts/ec2ba1c4e3a6417ba973d86ccb1c53a1/result.txt`.
- The corrected export contains `print(10 + 5)` as one code line and preserves later indented/commented examples such as `sum1 = 100 + 50     # 150 (100 + 50)`.
- The dynamic-page regression passed after the JavaScript change: 24 lazy-loaded records, 80 virtualized rows, 16 scroll steps, exit code 0.
- The production comment audit remains clean: `{}`.

The user's final visible Chrome/CLI bounded run `34870f0a746e4cf285371836ace76262` completed after six scroll steps and one stable scroll container, with 40 source blocks and no action-execution errors. It remains correctly classified as partial because two inline frames contain rendered SVG content that has not yet been visually extracted and verified. The later MCP diagnostic artifact above demonstrates the corrected code-block fidelity but does not remove that frame-coverage limitation.

### 2026-10-27 — Browser Use hostname classification, persistent cursor, and transport speed

Three real Browser Use attempts on W3Schools paused for unrelated advertising/cookie-synchronization document targets on `pbsj.bricks-co.com`, `eu-u.openx.net`, and `ups.analytics.yahoo.com`. The Browser Use CDP guard treated the first document in every attached page session as user-directed top-level navigation. It now records a hostname handoff only for the selected actor-page session or a child page attached during a bounded concrete agent-click interval. Incidental external document targets remain blocked without placing their tracker URL in the Streamlit authorization panel. Directly closing a target inside the Fetch callback was rejected after a real test showed Browser Use can expose its selected actor through an attached child session; the safe implementation blocks the request and leaves lifecycle cleanup to Browser Use.

Real Browser Use verification on the public W3Schools Operators page passed without an advertising-hostname prompt: **4 scrolls**, one stable requested content container, exact code preservation, page-boundary termination, and **6.3 seconds** for collection plus verification. The real local navigation-policy test also passed known-link blocking, external redirect blocking, popup blocking before network access, and a successful explicit hostname grant.

The red Windows-style cursor is now registered at document start for all three executors and installed before destination navigation. Native pointer input is dispatched in the same setup operation and immediately after navigation/click document replacement. Headed controlled-page tests for CLI, MCP, and Browser Use proved that cursor version `red-arrow-v2` exists before the first observation, lands inside the exact clicked target, and exists at a nonnegative real coordinate immediately after a full document replacement.

CLI/MCP collection now captures up to four sequential measured viewports inside one bounded executor call. Every intermediate viewport retains its own screenshot, rendered source, controls, links, and geometry; explicit user traversal limits disable prefetch. Stable-bottom grace remains mandatory, cached captures are invalidated by input/reset/navigation, and Stop can terminate the owned CLI/MCP operation. The final matching collection capture is reused for verification, removing a duplicate screenshot/DOM transport call without weakening source or coverage checks.

On the same real W3Schools bounded page test, Playwright CLI improved from **29.03 seconds to 16.59 seconds** and Playwright MCP from **12.72 seconds to 7.42 seconds** for collection plus verification. Provider response latency remains separate and can still dominate total task time. Real dynamic-content regressions after batching captured all **24 lazy records** and **80 virtualized rows**: MCP used 16 scroll movements in 14.33 seconds; CLI used 18 movements in 25.2 seconds. The final maintained suite passed **86 tests**; the production comment audit returned `{}`. Pytest still emits the previously documented Windows restricted temporary-directory cleanup warning after an exit code of 0. Streamlit health remains `ok` on port 8512.

### 2026-10-27 — General goal planning, entity deduplication, and autonomous research navigation

The LinkedIn job-search artifact `b289399302b64cd2a07aeb5fc0511cef` exposed repeated interface chrome and repeated logical records: its evidence store contained 752 blocks but only 204 unique text values, while generic labels such as `Jobs`, `Join now`, and `Sign in` appeared more than thirty times. The screenshots were not directly concatenated. The root defect was unstable DOM evidence identity: transient element IDs and changing viewport positions caused the same sticky or re-rendered content to be treated as new source.

The shared LangGraph workflow now compiles each instruction into a goal with requested entity, count, keywords, location, navigation scope, and completion criteria. A deterministic progress node checks unique qualifying records after each collection/action cycle. Repeated actions with no measured progress are rejected, task completion ends the run without unnecessary scrolling, and unsafe or irrelevant controls such as Join, Register, Apply, Subscribe, Purchase, Send, Delete, and Set alert are excluded from read-only research tasks.

Evidence identity now uses canonical page identity, stable DOM structure, logical record identity, and entity URLs rather than viewport position. Sticky controls are deduplicated across screenshots and re-renders. Finite entity requests export exactly the requested number of unique qualifying record containers while retaining the complete evidence manifest for audit. Exact rendered wording, headings, lists, tables, code indentation, order, and source URLs remain source-derived rather than model-summarized.

Cross-host navigation no longer pauses for every agent-selected research link. Direct navigation, an observed clicked link, its bounded redirect, and an intentionally opened popup are authorized for the current run. Advertising, analytics, delayed script redirects, unsafe schemes, and unrelated background popups remain blocked silently. Exact selected-host traversal and sibling subdomains remain automatic; no global allow-all browser policy was introduced.

Controlled real-browser validation after these changes:

- Playwright CLI collected exactly 10 unique matching records and stopped after 2 scroll movements.
- Playwright MCP collected exactly 10 unique matching records and stopped after 2 scroll movements.
- Browser Use collected exactly 10 unique matching records and stopped after 4 scroll movements.
- None of those three outputs included the repeated sticky `Jobs` or `Join now` controls.
- Deliberate external link, redirect, and popup navigation passed for CLI, MCP, and Browser Use without a hostname prompt.
- Existing static, lazy-loaded, virtualized, expandable, tabbed, paginated, shadow-DOM, and cursor-alignment regressions remain covered.
- The complete automated suite passed **92 tests**; the production comment audit returned `{}`.

These checks establish generalized executor and workflow behavior on controlled pages, not final acceptance of LinkedIn or every public website. A fresh credentialed run on the user's supplied real task remains required because public sites can impose login walls, CAPTCHA, anti-bot behavior, personalized layouts, and rate limits outside the agent's code.
