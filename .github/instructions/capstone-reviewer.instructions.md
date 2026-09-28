---
name: CAPSTONE Reviewer Chatbot
description: "Use when implementing or changing the CAPSTONE pull request reviewer chatbot, including its React UI, FastAPI services, GitHub and Google AI Studio integrations, review/chat flows, storage, security, or documentation."
---

# CAPSTONE Project Instructions

- Treat [prd.md](../../prd.md) as the product source of truth. Read the relevant requirements before changing behavior; do not silently expand v1 scope or replace its chosen technologies.
- Keep the frontend in React + TypeScript with Vite and the API/backend in Python with FastAPI. Keep GitHub and Google AI Studio access in server-side services, not browser code.
- Preserve the documented API purpose and data contracts. Validate review output against Pydantic models; every finding's file and line range must be grounded in the submitted diff. Handle large diffs by file/hunk and skip generated files, binaries, and lockfiles by default.
- Protect secrets: read GitHub and Google AI Studio credentials from server-side environment configuration; never expose or log them. Restrict CORS to the frontend origin, use least-privilege GitHub access, and handle upstream limits/timeouts with bounded retries and exponential backoff.
- Tell users before their first review that code is sent to Google AI Studio. Do not retain code beyond the session unless the user saves the session. The chatbot must not execute submitted code or its tests. Do not add PR-comment posting, auto-approval, or auto-merge behavior unless explicitly requested; posting findings is a stretch requirement.
- Keep chat answers grounded in the PR diff and findings. Preserve streaming for chat, useful loading/error/empty states, keyboard navigation, and WCAG AA contrast when changing the UI.
- Add or update focused tests for changed behavior, especially input validation, finding locations, secret handling, and failure/retry paths. Do not claim the product meets performance or quality targets without evidence.
- Treat the PRD's open questions as undecided. Ask before making product-level choices about accounts, OAuth versus personal tokens, maximum PR size, custom team rules, or model self-hosting.