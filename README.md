# Intelligent Browser Agent

Local Windows application with a Streamlit interface and one shared LangGraph agent. Each run uses one selected model and one actual browser executor.

## Run locally

The existing `.venv` contains the validated dependencies on this computer.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

For a fresh setup, use Python 3.12, Google Chrome, and Node.js 24:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm install -g @playwright/cli@0.1.22
npx --yes @playwright/mcp@0.0.83 --help
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If your virtual environment was created with uv and has no pip, install dependencies with `uv pip install --python .venv/Scripts/python.exe -r requirements.txt`. MCP uses the pinned local Node server; its first invocation requires network access for installation. The first Browser Use invocation may download its Chromium binary. No application code is sent to another hosted browser service.

## Use

1. Enter a website name, misspelling, domain, or URL and click **Search**. Real keyless web search provides up to five distinct hostname suggestions. Choose the intended result explicitly.
2. Enter the task. Choose Gemini or Groq in the sidebar, enter that provider's key in the masked field, and select exactly one browser method.
3. Use **Show browser window** for headful execution, or switch it off for headless execution. Start the task.
4. Watch current status, screenshots, and chronological diagnostic events. Pause, resume, or stop the owned run.
5. Complete login or CAPTCHA in the visible browser when requested, then click Resume. A headless run transfers eligible session state into a visible browser and restores headless mode afterward.
6. Inspect the exact text and download TXT, Markdown, or the evidence manifest. Partial results remain available when the task is blocked or stopped.

Provider and method checkboxes are mutually exclusive. Faded alternatives remain selectable. Changing configuration is disabled while its worker is actually alive.

## Fixed models and actual executors

| Selection | Actual implementation |
|---|---|
| Gemini | `gemini-3.5-flash-lite`, Google GenAI SDK, real screenshot image parts and JSON schema |
| Groq | `qwen/qwen3.8-27b`, Groq's OpenAI-compatible endpoint, screenshot image parts and strict JSON schema |
| Agent + Playwright MCP | `@playwright/mcp@0.0.83` over stdio, advertised evaluation/native-input/screenshot tools |
| Agent + Playwright CLI | `@playwright/cli@0.1.22`, isolated named CLI browser and trusted script files |
| Browser Use | `browser-use==0.11.13` low-level Browser/Page/Element APIs; LangGraph owns the reasoning |

Groq is the provider confirmed by the user at console.groq.com; it is different from xAI Grok. GPT-OSS 120B is excluded because this release requires the same selected model to handle screenshots and reasoning. There is no cross-provider or browser-method fallback.

The current fixed model IDs and image capabilities are documented by [Google](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) and [Groq](https://console.groq.com/docs/vision); Groq also documents [strict schema support](https://console.groq.com/docs/structured-outputs).

## Master-detail strategy & anti-detection architecture

For complex dual-pane applications (such as LinkedIn Jobs), the engine implements a specialized account-resilient master-detail strategy (`agent/strategies/linkedin.py`):

1. **In-page V8 execution loop**: Traversal, card activation, detail reading, and "Show More" expansion occur directly within Chromium's JavaScript runtime (`batch_script`). This eliminates excessive external Chrome DevTools Protocol (CDP) commands that trigger bot-detection heuristics (PerimeterX, Akamai, Cloudflare).
2. **Authentic Chrome fingerprint**: The agent binds directly to your installed Google Chrome binary (`channel="chrome"`, `--disable-blink-features=AutomationControlled`), utilizing native GPU hardware acceleration, authentic WebGL drivers, and real desktop color depths rather than generic headless Chromium footprints.
3. **Persistent profile warmth**: Browsing profiles are isolated per domain in `data/sessions/`, preserving session cookies, local storage, and IndexedDB state across runs. Anti-bot engines recognize the browser as an authentic returning user on an established desktop session.
4. **Humanized cursor animation**: A visible red arrow pointer overlay (`iba-cursor`) glides across targets with smooth CSS easing curves (`transition: left 0.08s ease-out, top 0.08s ease-out`) and realistic click ripple feedback, combined with natural randomized human delays (85ms–350ms).
5. **Instant desktop visibility**: On Windows, child processes launched from background threads often get hidden by the OS window manager. The engine invokes Win32 `OpenInputDesktop()`, `ShowWindowAsync(hwnd, SW_RESTORE)`, and `SetForegroundWindow(hwnd)` (`platform_core/windows.py`) right after `about:blank` launch, guaranteeing the browser is immediately visible on your physical screen.

## Source fidelity and traversal

The model chooses task-relevant regions, actions, and links. A deterministic collector traverses the actual rendered UI, captures each viewport before moving, handles discovered nested panels, and commits original source blocks into SQLite. It preserves code indentation, original values, headings, cells, and source-state relationships. Navigation prompt limits do not truncate stored source or downloads.

Finite tabs, expandable sections, load-more controls, button pagination with identifiable page semantics, and relevant links are traversed. A repeatedly growing feed asks for an explicit total traversal-action bound. A bounded result is marked partial rather than exhaustive. The agent follows task-relevant links automatically but requests explicit authorization before changing the exact selected hostname, including www/apex changes. Internal error pages (e.g. `chrome-error://`) and data URIs are automatically handled without false authorization stops.

Final text comes from captured source, never a model-written summary. TXT retains original internal block whitespace; blank lines separate UI blocks. Markdown adds structural encoding for headings, code, and tables. The manifest preserves raw blocks, table cell/span metadata, selected-tab/page context, URLs, and measured coverage. Markdown cannot reproduce arbitrary visual layout or merged cells exactly; TXT and the manifest remain authoritative.

Completion requires source, finite coverage, an exhausted relevant link frontier, and a same-model objective audit with quotations validated against the evidence store. In `agent/nodes.py`, finite entity extraction goals (`progress["complete"] == True`) automatically synchronize completion across graph checkpoints without false "Partial or blocked" reports.

## Boundaries and current limitations

This release supports information gathering, navigation, search, sorting, and filters. Purchases, sending messages, deletion, registration, website downloads, and downloaded-file processing are outside its scope.

Ordinary dialogs are dismissed; optional cookie consent is rejected. Necessary/login cookies remain permitted. Login and CAPTCHA require human assistance. Exact-host restrictions cover direct navigation, redirects, and popups.

Open shadow DOM is supported and tested. Embedded frames inside the requested extraction scope are currently reported as uninspected and prevent a full-completion claim. Closed shadow content, canvas/image-only source transcription, unusually delayed content without loading signals, and nonstandard pagination still require additional implementation or site-specific investigation. The selected vision model observes screenshots, but that is not a guarantee of exact visual transcription.

Assistance preserves cookies and current-origin local/session storage in memory. A browser restart cannot preserve arbitrary JavaScript memory or every site's IndexedDB-dependent flow. The resumed session is always re-observed. API keys remain runtime-only. Browser profiles and evidence may contain personal information from authorized tasks and stay in local application-managed storage.

The implemented dependency contracts are pinned. Browser Use popup interception chains a private CDP callback registry in the pinned version; cookie restoration uses its pinned CDP helper. Upgrading that library requires rerunning the real browser tests.

## Tests and verification

The test suite contains **108 unit tests passing**:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/
```

Key test coverage areas:
- `test_linkedin_strategy.py`: Master-detail card matching, detail extraction, resume mechanics, and batch payload parsing.
- `test_agent_nodes.py`: Graph cycle transitions, finite entity progress acceptance, and multi-cycle verification.
- `test_browser_use_intent.py`: Hostname navigation intent, CDP paused request filtering, and authorization safety.
- `test_completion_evidence.py`: Evidence store integrity, citation auditing, and manifest serialization.
- `test_vision_providers.py`: Strict schema enforcement, multimodal image parts, and model routing.
- `test_browser_adapters.py`: Playwright MCP, Playwright CLI, and Browser Use contract validation.

Production Python modules have module/class/function docstrings and explanatory comments above executable statements, following the user's requested style. Read [the architecture and root-cause changes](docs/ARCHITECTURE_AND_CHANGES.md) and [the validation record](docs/VALIDATION_STATUS.md) for full historical detail.
