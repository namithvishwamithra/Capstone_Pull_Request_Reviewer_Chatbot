---
name: capstone-python-fastapi
description: 'Implement, debug, or test the CAPSTONE pull request reviewer backend in Python and FastAPI. Use for API routes, GitHub ingestion, diff parsing/chunking, Gemma/Google AI Studio review and chat, Pydantic validation, sessions, storage, security, or backend tests.'
argument-hint: 'Describe the backend endpoint, service, defect, or test to address.'
---

# CAPSTONE Python and FastAPI Backend

Implement server-side CAPSTONE behavior with reliable contracts, grounded review findings, and protected credentials.

## Workflow

1. Read the relevant requirements in `prd.md` and the CAPSTONE project instructions. The PRD is the product source of truth; keep its undecided questions undecided.
2. Inspect the existing app layout, route/service boundaries, dependency configuration, Pydantic models, storage layer, and test conventions before editing. Preserve established patterns and avoid introducing a new framework or dependency without a concrete need.
3. Define or confirm the HTTP and data contract first. The documented API includes review creation/retrieval, streaming chat, session listing, Markdown export, and health check. Do not change endpoint behavior or payload formats without checking callers and tests.
4. Keep GitHub API and Google AI Studio calls in server-side services. Read credentials from server-side environment configuration; never return, log, or expose token/API-key values. Restrict CORS to the frontend origin and use least-privilege GitHub access.
5. Validate incoming data and model output. Represent findings with Pydantic models and the documented severity/category and location fields. Verify each finding's file and line range against the submitted diff; reject or repair unsupported locations rather than trusting model claims.
6. For PR diffs, parse and chunk by file/hunk when needed; skip generated files, binaries, and lockfiles by default. Do not execute submitted code or tests. Keep chunk sizing tied to the configured model/context constraints instead of inventing a product maximum.
7. Make upstream calls resilient: bounded timeouts, rate-limit handling, bounded retries with exponential backoff, and clear errors. For structured model output, use the configured low-temperature review flow and, if validation fails, at most the PRD-specified single repair attempt. Preserve streaming for chat.
8. Respect privacy: disclose before a user's first review that code is sent to Google AI Studio. Do not retain code past the session unless the user saves the session. Do not add logging that stores submitted code or secrets.
9. Add or update focused tests for request validation, diff-grounded finding locations, malformed model output, secret handling, retry/timeout/rate-limit behavior, and streaming/session behavior relevant to the change. Use existing fixtures and test tooling.
10. Run relevant tests and available type/lint checks. State precisely what passed or failed. Do not claim performance, reliability, or evaluation targets are met without measurements.

## Guardrails

- Do not add auto-approval, auto-merge, or PR-comment posting unless explicitly requested; posting findings is a stretch requirement.
- Do not assume authentication/account model, OAuth versus personal tokens, maximum PR size, custom team rules, or self-hosting; ask before making those product choices.
- Keep assistant answers grounded in the submitted PR diff and prior findings; do not allow unsupported files or line ranges into API responses.
- Keep secrets and user code out of logs, exception text returned to clients, and persisted data outside the explicitly saved-session flow.