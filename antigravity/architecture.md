**INTELLIGENT BROWSER AGENT**

# System Architecture

Components, LangGraph workflow, browser adapters, state, and execution flow

Version: 1.0 Status: Initial specification

## 1. Architecture Summary

The system separates the Streamlit experience, LangGraph reasoning workflow, model-provider integration, browser-method adapters, and runtime state. The selected browser adapter executes actions while the same agent workflow owns observation, decision-making, verification, and recovery.

## 2. Logical Components

| Component | Responsibilities |
| --- | --- |
| Streamlit UI | Website search/selection, task input, model and key selection, browser-method selection, visibility toggle, run controls, live monitoring. |
| Website Discovery | Search dynamically and return 3–5 distinguishable candidates for user confirmation. |
| LangGraph Agent | Maintain task state; interpret the objective; inspect observations; choose actions; verify outcomes; manage recovery and completion. |
| Model Provider Adapter | Normalize Gemini and Grok requests/responses. The selected provider handles all LLM-based reasoning for the run. |
| Browser Adapter | Provide a consistent action/observation contract for Playwright MCP, Playwright CLI, or Browser Use. |
| Session and Run State | Track website, task, browser context, observations, retry counters, status, logs, screenshots, and output. |
| Local Runtime | Run Streamlit, LangGraph, browser processes, and temporary run artifacts locally. |

## 3. End-to-End Execution Flow

| Step | Flow |
| --- | --- |
| 1. Configure | User selects a website, enters a task, chooses one model and API key, selects one browser method, and sets visibility. |
| 2. Initialize | Create run state, resolve or create the reusable browser session, and open the selected website. |
| 3. Observe | Collect a screenshot and available structured state such as URL, page text, accessibility data, and element information. |
| 4. Decide | Send task context and relevant observations to the selected LLM; receive the next action or a completion/recovery decision. |
| 5. Act | Execute the action through the selected browser adapter and capture the outcome. |
| 6. Verify | Observe the updated state and determine whether the action achieved its intended effect. |
| 7. Recover or continue | Diagnose failures, adapt the approach, and retry within the per-decision limit; otherwise continue the loop. |
| 8. Finish | Present requested information or a blocker; keep current-run monitoring artifacts available until the next run starts. |

## 4. LangGraph Nodes and State

| Node | Purpose |
| --- | --- |
| Task Interpreter | Identify the objective and task-relevant completion conditions. |
| Observer | Normalize screenshot and structured browser data into a compact observation. |
| Decision Maker | Use the selected LLM and current state to choose the next action. |
| Action Executor | Validate and dispatch the action through the selected browser adapter. |
| Verifier | Check resulting state and determine action success. |
| Recovery Manager | Classify failures, choose revised strategies, and track attempts for the current decision. |
| Run Controller | Handle completion, manual stop, status updates, blockers, and current-run lifecycle. |

## 5. Browser Adapter Contract

Each method should expose a common logical contract: initialize or attach to a browser context; observe the current page; perform a supported action; manage navigation and relevant tabs/windows; configure headful/headless behavior where supported; and return normalized outcomes or errors. Method-specific command formats remain inside the adapter.

## 6. State and Failure Paths

- Run state includes objective, selected domain, provider/method, browser context, current observation, action history, retry count, status, logs, screenshots, and output.
- Session state is separated by website and execution context to support appropriate reuse.
- API keys are runtime secrets and are excluded from logs and user-visible errors.
- Invalid credentials produce an actionable error; browser failures enter recovery; expired sessions allow user-assisted sign-in; Stop cancels active work.
- The selected website is the default navigation boundary. External-site navigation requires explicit user authorization.

## 7. Design Principle

Keep the reasoning provider, browser execution method, and visibility mode as independent configuration dimensions. This allows the same agent workflow to operate through any selected browser method and either supported model provider.
