# Architecture and root-cause changes

Implementation authorized by the user on 26 October 2026, after the requirements review and model/provider clarifications. Detailed explanatory comments are required throughout new and modified code.

## Requirements precedence

The five detailed specifications are `antigravity/prd.md`, `trd.md`, `architecture.md`, `specs.md`, and `implementation_plan (1).md`; the folder also contains a README. The user's original requirements and later explicit decisions override contradictions in those documents. Their confirmed second provider is Groq, with Qwen 3.8 27B; references to xAI Grok or GPT-OSS as the screenshot model are superseded.

The original pre-change source was preserved outside the project in:

`C:/Users/Admin/.codex/visualizations/2026/10/26/01a1781f-b11d-7c43-8790-d0de10a1d1bc/source-before-implementation-20261026-194236.zip`

Credentials, browser profiles, and private runtime artifacts were excluded.

## Runtime ownership

`app.py -> ui/view.py -> services/worker.py -> services/run_controller.py -> agent/graph.py`

Streamlit owns presentation and explicit user decisions. One spawned Windows worker owns the selected provider, browser, LangGraph, and SQLite evidence. Commands/events connect the worker to the responsive UI. Credentials and runtime objects never enter graph checkpoints.

Each bounded graph cycle observes, decides, acts, verifies, and routes failures to recovery. The controller checkpoints data-only state between cycles and handles human assistance. There is no hidden global task step cutoff. Repeated actual failures or no-progress cycles stop honestly.

Adapters implement genuine MCP, CLI, and Browser Use transports. Shared inspection, target validation, exact-host rules, traversal, source evidence, and completion checks live above those transports.

## Problems corrected at their responsible boundaries

| Previous failure | Root cause addressed | Resulting behavior |
|---|---|---|
| Extremely slow scrolling | Model calls and repeated transport startup for mechanical viewport work; animation/fixed delays | Browser-local measured readiness; instant overlapping scrolls; one batched CLI/MCP operation for movement, stable source, and screenshot |
| Wrong clicks/cursor drift | Positional/ambiguous target references and an independently animated pointer | Stable concrete node IDs, originating observation validation, unique native target resolution, actionability checks; passive pointer listens to real native mouse movement |
| Summarized or invented output | Model final prose and fallback finish decisions replacing captured page source | Deterministic evidence-backed TXT/Markdown assembly; no click/blocked-to-finish coercion; source-supported completion audit |
| Missing below-fold content | Fixed small scan limits and prompt-sized text treated as full source | All finite viewport/container traversal, capture-before-move, delayed-loading checks, persistent evidence outside prompt limits |
| Virtual rows lost or duplicated | DOM replacement and text-only deduplication | Logical row identity, exact source versions, source-state and cell relationships |
| Tabs/pages interleaved or missed | Replaced content reused prior coverage; pagination and tab changes lost earlier view | Capture each current tab's finite pages before switching; state order retained; same-URL filter/click changes invalidate stale coverage |
| False success | Tool return/nonempty text treated as objective completion | Independent observed effects, finite coverage, frontier accounting, exact quotations and same-model semantic audit |
| Lost failures | Error/outcome fields outside declared graph channels and reset on unverified replies | Declared serializable channels, retained sanitized causes/history, bounded retries |
| UI unresponsive / misleading Stop | Browser/model work on UI thread; detached CLI daemon outside worker ancestry | Worker isolation, live event polling, bounded normal cleanup, creation-time-validated process ownership for detached browsers |
| Broken model integration | Wrong Grok/Groq naming, unavailable/text-only model, screenshot paths supplied as text | Correct fixed Gemini and Groq Qwen models, actual image parts and strict structured request contracts |
| Website suggestions fabricated/empty | Guessed domain fallbacks and obsolete search package | Maintained keyless DDGS search, validated actual URLs, explicit selection; full user-entered URL remains usable if search fails |
| Redirect/popup host escapes | Validation after navigation; popup request before frame creation | Top-level interception before forbidden network access; explicit exact-host authorization and retry |
| Headless assistance loses login | Browser shutdown/profile flush insufficient; MCP reader reused another generation's queue | In-memory cookie/current-origin storage transfer before navigation; per-connection MCP reader/queue; visible assistance then original visibility restored |
| Global Windows launch interference | Process-launch monkeypatch | Normal runtime startup; no global CreateProcess monkeypatch |
| Delayed browser window appearance | Child processes hidden by Windows OS window manager | Win32 `OpenInputDesktop()`, `ShowWindowAsync(hwnd, SW_RESTORE)`, and `SetForegroundWindow(hwnd)` verified right after launching `about:blank` |
| Browser Use async evaluation returning empty Promises | Synchronous `() => (source)()` wrapper returning unawaited pending Promise | Dynamic `(async () => await (source)())` wrapper ensuring in-browser async operations resolve before returning to Python |
| Transient internal error blocking navigation | `chrome-error://chromewebdata/` treated as unauthorized external domain | Internal browser error schemes (`chrome-error:`, `chrome:`, `about:`, `data:`) recognized and bypassed without triggering `AuthorizationRequired` gates |
| Premature "Partial or blocked" on finite goals | Verification requiring link frontier exhaustion across all earlier pages | Verification accepts finite progress completion (`progress["complete"] == True`) and synchronizes page state |
| Bot detection on high-frequency listings (LinkedIn) | External CDP synthetic mouse commands triggering edge bot detection (PerimeterX, Akamai) | In-page V8 execution loop (`LinkedInStrategy`), humanized bezier/CSS cursor overlay, authentic installed Google Chrome binary with persistent profile |
| Form submission friction in Streamlit | Default textareas requiring `Ctrl+Enter` | Client-side key handler enabling standard `Enter` key submission without requiring `Ctrl+Enter` |

## Important file responsibilities

- `models/base.py`: constrained response schema, bounded navigation context, image inventory, exact-source objective proof.
- `models/gemini_provider.py`, `groq_provider.py`: actual selected-provider multimodal requests; explicit access/configuration failure; no fallback.
- `agent/strategies/linkedin.py`: account-resilient, anti-detection master-detail job extraction; high-speed in-browser traversal; humanized gliding cursor and click ripples.
- `agent/nodes.py`: grounded decisions, finite entity completion verification, complete link review, independent effect/source verification and honest recovery.
- `browser/base.py`: stable observations, authorization, native input policy, internal scheme bypass, shared batch traversal and session transfer.
- `browser/page_probe.js`: rendered controls, stable IDs, source blocks, logical virtual rows, geometry and scroll containers.
- `browser/settle_probe.js`: bounded browser-local source/load readiness.
- `browser/native_playwright.js`: genuine native MCP/CLI input and pre-navigation host interception.
- `browser/cursor_init.js`: passive browser-local pointer driven by actual events.
- `browser/playwright_mcp.py`, `playwright_cli.py`, `browser_use.py`: actual executor lifecycle, immediate visible window verification, async evaluate wrappers, and transport.
- `platform_core/windows.py`: Win32 desktop verification, window restore/focus, process group management.
- `services/extraction.py`: finite traversal, tabs/expanders/load-more/pagination, stable-end coverage and explicit non-finite scope decisions.
- `services/evidence.py`: durable exact source, identity/state ordering, TXT/Markdown/manifest export.
- `services/worker.py`: spawn-safe ownership, streaming events, Pause/Stop, proved detached-browser cleanup, partial recovery after forced exit.
- `ui/view.py`: exclusive checkbox configuration, website-first flow, live screenshots/status, explicit assistance, exact results/downloads.
- `tools/check_comments.py`: read-only AST audit of module/class/function documentation and explanations for executable production statements.

## Completion and remaining acceptance

The browser fixtures prove specific behaviors, not arbitrary website reliability. Live model task selection and reasoning have not been verified with the user's API credentials. The user must supply their real websites and exact tasks for acceptance. Embedded frames and image/canvas-only transcription remain known unsupported extraction cases; they are not covered by the passing fixture matrix. See the validation record for exact results and limits.
